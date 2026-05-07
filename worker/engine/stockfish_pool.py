"""Process-level Stockfish singleton.

One engine instance per worker process. Celery --concurrency=2 means
two worker processes → two independent Stockfish instances.
"""
from __future__ import annotations

import os
import signal
from typing import Optional

import chess
import chess.engine

_engine: Optional[chess.engine.SimpleEngine] = None

STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")
ANALYSIS_TIMEOUT = 10  # seconds — hard kill if Stockfish hangs


def get_engine() -> chess.engine.SimpleEngine:
    global _engine
    if _engine is None or _engine.transport.is_dead():
        _engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        _engine.configure({"Threads": 1, "Hash": 64})
    return _engine


def close_engine() -> None:
    global _engine
    if _engine is not None:
        try:
            _engine.quit()
        except Exception:
            pass
        _engine = None


def analyse(board: chess.Board, depth: int, multipv: int = 1) -> list[chess.engine.InfoDict]:
    """Run Stockfish analysis with a hard timeout. Returns list of InfoDicts (one per PV)."""
    engine = get_engine()
    try:
        result = engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
            multipv=multipv,
        )
        # engine.analyse with multipv returns a list; without, a single dict
        if isinstance(result, list):
            return result
        return [result]
    except chess.engine.EngineTerminatedError:
        close_engine()
        return []
    except Exception:
        # On timeout or weird positions, kill and restart
        close_engine()
        return []
