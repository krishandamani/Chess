"""Game ingestion tasks: fetch from Chess.com and Lichess."""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
import psycopg2

from celery_app import celery_app

DATABASE_URL = os.getenv("DATABASE_URL", "")

CHESSCOM_USER_AGENT = "repertoire/0.1 (contact: chess@example.com)"
RAPID_CLASSICAL_TIME_CONTROLS = {"rapid", "classical", "daily"}

# Map Chess.com time-class strings to our internal values
CHESSCOM_TIME_CLASS_MAP = {
    "rapid": "rapid",
    "classical": "classical",
    "daily": "daily",
}

LICHESS_PERF_TYPES = "rapid,classical,correspondence"


def _get_conn():
    return psycopg2.connect(DATABASE_URL)


def _backoff_request(client: httpx.Client, url: str, headers: dict, retries: int = 4) -> Optional[httpx.Response]:
    delay = 2
    for attempt in range(retries):
        resp = client.get(url, headers=headers, timeout=30)
        if resp.status_code == 429:
            time.sleep(delay)
            delay *= 2
            continue
        return resp
    return None


# ── Chess.com ──────────────────────────────────────────────────────────────────

def _fetch_chesscom_games(conn, user_id: str, chesscom_username: str, limit_months: Optional[int] = None) -> list[str]:
    """Fetch games from Chess.com. Returns list of game_ids inserted."""
    cur = conn.cursor()
    headers = {"User-Agent": CHESSCOM_USER_AGENT}
    game_ids: list[str] = []

    with httpx.Client() as client:
        resp = _backoff_request(client, f"https://api.chess.com/pub/player/{chesscom_username}/games/archives", headers)
        if not resp or resp.status_code != 200:
            return game_ids

        archives: list[str] = resp.json().get("archives", [])
        if limit_months:
            archives = archives[-limit_months:]

        for archive_url in archives:
            resp2 = _backoff_request(client, archive_url, headers)
            if not resp2 or resp2.status_code != 200:
                continue

            games = resp2.json().get("games", [])
            for g in games:
                time_class = g.get("time_class", "")
                if time_class not in CHESSCOM_TIME_CLASS_MAP:
                    continue

                external_id: str = g.get("url", "").split("/")[-1] or str(uuid.uuid4())
                pgn: str = g.get("pgn", "")
                if not pgn:
                    continue

                white = g.get("white", {})
                black = g.get("black", {})
                username_lower = chesscom_username.lower()
                user_is_white = white.get("username", "").lower() == username_lower
                user_color = "white" if user_is_white else "black"
                user_rating = (white if user_is_white else black).get("rating")
                opp_rating = (black if user_is_white else white).get("rating")

                end_time = g.get("end_time", 0)
                played_at = datetime.fromtimestamp(end_time, tz=timezone.utc) if end_time else datetime.now(tz=timezone.utc)

                result_map = {"win": "1-0" if user_is_white else "0-1",
                              "lose": "0-1" if user_is_white else "1-0",
                              "agreed": "1/2-1/2", "repetition": "1/2-1/2",
                              "stalemate": "1/2-1/2", "insufficient": "1/2-1/2",
                              "50move": "1/2-1/2", "timevsinsufficient": "1/2-1/2"}
                user_result = (white if user_is_white else black).get("result", "")
                result = result_map.get(user_result, "1/2-1/2")

                # ECO from PGN headers
                eco_code = None
                opening_name = None
                for line in pgn.split("\n"):
                    if line.startswith('[ECO '):
                        eco_code = line.split('"')[1] if '"' in line else None
                    elif line.startswith('[Opening ') or line.startswith('[ECOUrl '):
                        if line.startswith('[Opening '):
                            opening_name = line.split('"')[1] if '"' in line else None

                headers_json = json.dumps({
                    "White": white.get("username", ""),
                    "Black": black.get("username", ""),
                    "TimeControl": g.get("time_control", ""),
                    "Result": result,
                })

                try:
                    cur.execute(
                        """
                        INSERT INTO games
                            (user_id, source, external_id, played_at, time_control, result,
                             user_color, user_rating, opponent_rating, eco_code, opening_name,
                             pgn, headers)
                        VALUES (%s, 'chesscom', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, source, external_id) DO NOTHING
                        RETURNING id::text
                        """,
                        (user_id, external_id, played_at, CHESSCOM_TIME_CLASS_MAP[time_class],
                         result, user_color, user_rating, opp_rating,
                         eco_code, opening_name, pgn, headers_json),
                    )
                    row = cur.fetchone()
                    if row:
                        game_ids.append(row[0])
                except Exception:
                    conn.rollback()
                    continue

    conn.commit()
    cur.close()
    return game_ids


# ── Lichess ────────────────────────────────────────────────────────────────────

def _fetch_lichess_games(conn, user_id: str, lichess_username: str, since_ms: Optional[int] = None) -> list[str]:
    """Fetch games from Lichess via NDJSON streaming."""
    cur = conn.cursor()
    game_ids: list[str] = []

    params = {
        "perfType": LICHESS_PERF_TYPES,
        "pgnInJson": "true",
        "clocks": "true",
        "max": "500",
    }
    if since_ms:
        params["since"] = str(since_ms)

    url = f"https://lichess.org/api/games/user/{lichess_username}"
    headers = {
        "Accept": "application/x-ndjson",
        "User-Agent": CHESSCOM_USER_AGENT,
    }

    with httpx.Client() as client:
        with client.stream("GET", url, params=params, headers=headers, timeout=120) as resp:
            if resp.status_code != 200:
                return game_ids

            for line in resp.iter_lines():
                if not line.strip():
                    continue
                try:
                    g = json.loads(line)
                except json.JSONDecodeError:
                    continue

                perf = g.get("perf", "")
                if perf not in {"rapid", "classical", "correspondence"}:
                    continue

                external_id = g.get("id", str(uuid.uuid4()))
                pgn = g.get("pgn", "")
                players = g.get("players", {})
                white_p = players.get("white", {})
                black_p = players.get("black", {})

                username_lower = lichess_username.lower()
                user_is_white = white_p.get("user", {}).get("name", "").lower() == username_lower
                user_color = "white" if user_is_white else "black"
                user_rating = (white_p if user_is_white else black_p).get("rating")
                opp_rating = (black_p if user_is_white else white_p).get("rating")

                status = g.get("status", "")
                winner = g.get("winner")
                if winner == "white":
                    result = "1-0"
                elif winner == "black":
                    result = "0-1"
                else:
                    result = "1/2-1/2"

                created_at_ms = g.get("createdAt", 0)
                played_at = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc) if created_at_ms else datetime.now(tz=timezone.utc)

                opening = g.get("opening", {})
                eco_code = opening.get("eco")
                opening_name = opening.get("name")

                time_control_map = {"rapid": "rapid", "classical": "classical", "correspondence": "daily"}
                time_control = time_control_map.get(perf, "rapid")

                headers_json = json.dumps({
                    "White": white_p.get("user", {}).get("name", ""),
                    "Black": black_p.get("user", {}).get("name", ""),
                    "Result": result,
                    "Variant": g.get("variant", "standard"),
                })

                if not pgn:
                    continue

                try:
                    cur.execute(
                        """
                        INSERT INTO games
                            (user_id, source, external_id, played_at, time_control, result,
                             user_color, user_rating, opponent_rating, eco_code, opening_name,
                             pgn, headers)
                        VALUES (%s, 'lichess', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, source, external_id) DO NOTHING
                        RETURNING id::text
                        """,
                        (user_id, external_id, played_at, time_control,
                         result, user_color, user_rating, opp_rating,
                         eco_code, opening_name, pgn, headers_json),
                    )
                    row = cur.fetchone()
                    if row:
                        game_ids.append(row[0])
                except Exception:
                    conn.rollback()
                    continue

    conn.commit()
    cur.close()
    return game_ids


# ── Orchestrator task ──────────────────────────────────────────────────────────

@celery_app.task(name="tasks.ingest.fetch_and_analyze", bind=True, max_retries=2)
def fetch_and_analyze(self, user_id: str, job_id: str, kind: str, days: int = 30) -> None:
    conn = _get_conn()
    cur = conn.cursor()

    try:
        # Mark job as running
        cur.execute(
            "UPDATE analysis_jobs SET status = 'running', started_at = now() WHERE id = %s",
            (job_id,),
        )
        conn.commit()

        # Get user's chess usernames
        cur.execute(
            "SELECT chesscom_username, lichess_username FROM profiles WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Profile not found: {user_id}")
        chesscom_username, lichess_username = row

        game_ids: list[str] = []

        limit_months = 2 if kind == "initial_recent" else None
        since_ms = int((time.time() - days * 86400) * 1000) if kind == "incremental" else None

        if chesscom_username:
            game_ids.extend(_fetch_chesscom_games(conn, user_id, chesscom_username, limit_months=limit_months))

        if lichess_username:
            game_ids.extend(_fetch_lichess_games(conn, user_id, lichess_username, since_ms=since_ms))

        # Update total count
        cur.execute(
            "UPDATE analysis_jobs SET games_total = %s WHERE id = %s",
            (len(game_ids), job_id),
        )
        conn.commit()

        # Queue analysis for each game
        for gid in game_ids:
            celery_app.send_task(
                "tasks.analyze.analyze_game",
                kwargs={"game_id": gid, "user_id": user_id, "job_id": job_id},
                queue="analysis",
            )

        # If no games, mark done immediately
        if not game_ids:
            cur.execute(
                "UPDATE analysis_jobs SET status = 'done', finished_at = now() WHERE id = %s",
                (job_id,),
            )
            conn.commit()

    except Exception as exc:
        try:
            cur.execute(
                "UPDATE analysis_jobs SET status = 'failed', error = %s, finished_at = now() WHERE id = %s",
                (str(exc), job_id),
            )
            conn.rollback()
            conn.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        cur.close()
        conn.close()
