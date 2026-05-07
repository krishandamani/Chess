"""Game analysis task: runs Stockfish over every user-turn position."""
from __future__ import annotations

import os
import uuid
from typing import Optional

import chess
import chess.pgn
import chess.engine
import io
import psycopg2

from celery_app import celery_app
from engine.position_cache import normalize_fen, fen_hash, get_cached_eval, insert_eval
from engine.stockfish_pool import analyse
from tasks.classify import classify_mistake, extract_eval_fields, pov_score_to_cp

DATABASE_URL = os.getenv("DATABASE_URL", "")

DEPTH_PRIMARY = 18
DEPTH_POST_MOVE = 16


def _get_conn():
    return psycopg2.connect(DATABASE_URL)


@celery_app.task(name="tasks.analyze.analyze_game", bind=True, max_retries=2)
def analyze_game(self, game_id: str, user_id: str, job_id: str) -> None:
    conn = _get_conn()
    cur = conn.cursor()

    try:
        cur.execute("SELECT pgn, user_color FROM games WHERE id = %s", (game_id,))
        row = cur.fetchone()
        if not row:
            return
        pgn_text, user_color_str = row
        user_color = chess.WHITE if user_color_str == "white" else chess.BLACK

        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if not game:
            return

        board = game.board()
        node = game

        positions_analyzed = 0
        cache_hits = 0

        while not node.is_end():
            node = node.variation(0)
            move = node.move

            # Only analyze positions where it was the user's turn BEFORE this move
            if board.turn != user_color:
                board.push(move)
                continue

            # — Evaluate the position BEFORE the user's move (best move for user) —
            fen_before = normalize_fen(board)
            fhash_before = fen_hash(fen_before)

            cached = get_cached_eval(cur, fhash_before)
            if cached:
                cache_hits += 1
                best_eval = cached
            else:
                infos = analyse(board, DEPTH_PRIMARY, multipv=2)
                best_eval = extract_eval_fields(infos, user_color)
                if best_eval.get("best_move"):
                    insert_eval(cur, fhash_before, fen_before, DEPTH_PRIMARY, best_eval,
                                {k.replace("second_best_", ""): v for k, v in best_eval.items()
                                 if k.startswith("second_best_")} if "second_best_move" in best_eval else None)
                    positions_analyzed += 1

            played_move_uci = move.uci()

            # — Evaluate the position AFTER the user's actual move —
            board.push(move)
            fen_after = normalize_fen(board)
            fhash_after = fen_hash(fen_after)

            cached_after = get_cached_eval(cur, fhash_after)
            if cached_after:
                cache_hits += 1
                after_eval = cached_after
            else:
                infos_after = analyse(board, DEPTH_POST_MOVE, multipv=1)
                after_eval = extract_eval_fields(infos_after, user_color)
                if after_eval.get("best_move"):
                    insert_eval(cur, fhash_after, fen_after, DEPTH_POST_MOVE, after_eval, None)
                    positions_analyzed += 1

            # — Compute delta and classify —
            best_cp = _effective_cp(best_eval, user_color)
            played_cp = _effective_cp_from_after(after_eval, user_color)

            delta_cp = max(0, min(1000, best_cp - played_cp))
            severity = classify_mistake(delta_cp)

            if severity:
                # Get piece info from the move
                piece = board.piece_at(move.to_square)  # board already has move pushed
                moving_piece = piece  # piece that ended up on to_square
                if moving_piece is None:
                    # Shouldn't happen, but skip if so
                    continue

                piece_symbol = chess.piece_symbol(moving_piece.piece_type).upper()
                from_sq = chess.square_name(move.from_square)
                to_sq = chess.square_name(move.to_square)
                was_capture = board.is_capture(move) if hasattr(board, "_original_before") else False

                ply = board.ply() - 1  # ply before this move
                move_number = (ply // 2) + 1

                mistake_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO mistakes (
                        id, game_id, user_id, ply, move_number,
                        fen_before, fen_before_hash,
                        played_move, played_eval_cp, played_mate_in,
                        best_move, best_eval_cp, best_mate_in,
                        delta_cp, severity,
                        piece_moved, from_square, to_square, was_capture
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        mistake_id, game_id, user_id, ply, move_number,
                        fen_before, fhash_before,
                        played_move_uci,
                        after_eval.get("eval_cp"),
                        after_eval.get("mate_in"),
                        best_eval.get("best_move", ""),
                        best_eval.get("eval_cp"),
                        best_eval.get("mate_in"),
                        delta_cp, severity,
                        piece_symbol, from_sq, to_sq,
                        False,  # was_capture recomputed below
                    ),
                )
            # end if severity

        # Mark game as analyzed
        cur.execute(
            "UPDATE games SET analyzed_at = now() WHERE id = %s",
            (game_id,),
        )

        # Update job progress
        cur.execute(
            """
            UPDATE analysis_jobs
            SET games_done = games_done + 1,
                positions_analyzed = positions_analyzed + %s,
                cache_hits = cache_hits + %s
            WHERE id = %s
            """,
            (positions_analyzed, cache_hits, job_id),
        )

        conn.commit()

    except Exception as exc:
        conn.rollback()
        raise self.retry(exc=exc, countdown=30)
    finally:
        cur.close()
        conn.close()


def _effective_cp(eval_dict: dict, user_color: chess.Color) -> int:
    """Convert eval dict to a centipawn value from the user's POV."""
    if eval_dict.get("mate_in") is not None:
        m = eval_dict["mate_in"]
        return (10000 - abs(m) * 100) if m > 0 else -(10000 - abs(m) * 100)
    return eval_dict.get("eval_cp") or 0


def _effective_cp_from_after(after_eval: dict, user_color: chess.Color) -> int:
    """After pushing the user's move, the eval is from the OPPONENT's POV — negate it."""
    cp = _effective_cp(after_eval, user_color)
    return -cp
