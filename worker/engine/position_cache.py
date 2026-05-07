"""FEN normalization and position_evals cache helpers."""
from __future__ import annotations

import hashlib
from typing import Optional

import chess


def normalize_fen(board: chess.Board) -> str:
    """Return a canonical FEN for cache keying.

    Two positions that are strategically identical but differ only in
    half-move clock or en-passant availability (when no pawn can legally
    capture en-passant) should hash to the same key.
    """
    # Work on a copy so we don't mutate the caller's board
    b = board.copy()

    # Zero out the halfmove clock — irrelevant for eval
    b.halfmove_clock = 0

    # Clear en passant square if no pawn can actually capture it
    if b.ep_square is not None:
        can_capture = False
        for sq in b.attackers(b.turn, b.ep_square):
            piece = b.piece_at(sq)
            if piece and piece.piece_type == chess.PAWN:
                can_capture = True
                break
        if not can_capture:
            b.ep_square = None

    return b.fen()


def fen_hash(fen: str) -> str:
    return hashlib.sha1(fen.encode()).hexdigest()


def get_cached_eval(conn, fhash: str) -> Optional[dict]:
    """Look up position_evals by fen_hash. Returns a dict or None."""
    row = conn.execute(
        "SELECT * FROM position_evals WHERE fen_hash = %s",
        (fhash,),
    ).fetchone()
    if row is None:
        return None
    columns = [desc[0] for desc in conn.description]
    return dict(zip(columns, row))


def insert_eval(conn, fhash: str, fen: str, depth: int, info_primary: dict, info_secondary: Optional[dict]) -> None:
    """Persist a Stockfish result into position_evals."""
    conn.execute(
        """
        INSERT INTO position_evals
            (fen_hash, fen, depth, eval_cp, mate_in, best_move, best_line,
             second_best_move, second_best_eval_cp, second_best_mate_in)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (fen_hash) DO UPDATE
            SET depth = EXCLUDED.depth,
                eval_cp = EXCLUDED.eval_cp,
                mate_in = EXCLUDED.mate_in,
                best_move = EXCLUDED.best_move,
                best_line = EXCLUDED.best_line,
                second_best_move = EXCLUDED.second_best_move,
                second_best_eval_cp = EXCLUDED.second_best_eval_cp,
                second_best_mate_in = EXCLUDED.second_best_mate_in,
                computed_at = now()
        WHERE position_evals.depth < EXCLUDED.depth
        """,
        (
            fhash,
            fen,
            depth,
            info_primary.get("eval_cp"),
            info_primary.get("mate_in"),
            info_primary["best_move"],
            info_primary.get("best_line", ""),
            info_secondary["best_move"] if info_secondary else None,
            info_secondary.get("eval_cp") if info_secondary else None,
            info_secondary.get("mate_in") if info_secondary else None,
        ),
    )
    conn.connection.commit()
