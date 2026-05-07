"""Mistake classification from centipawn loss."""
from __future__ import annotations

from typing import Optional

import chess
import chess.engine

MATE_SCORE = 10000
MATE_CP_BASE = 10000


def pov_score_to_cp(score: chess.engine.PovScore, user_color: chess.Color) -> int:
    """Convert a PovScore to centipawns from the user's point of view.

    Mate scores are mapped to ±(MATE_CP_BASE - |mate_in| * 100) so that
    a mate-in-1 is worth 9900, mate-in-2 is 9800, etc.
    """
    relative = score.pov(user_color)
    if relative.is_mate():
        m = relative.mate()
        if m > 0:
            return MATE_CP_BASE - m * 100   # user is mating
        else:
            return -(MATE_CP_BASE + m * 100)  # user is being mated (m is negative)
    cp = relative.score()
    return max(-MATE_CP_BASE, min(MATE_CP_BASE, cp if cp is not None else 0))


def classify_mistake(delta_cp: int) -> Optional[str]:
    """Return severity label or None if the move was acceptable."""
    if delta_cp < 50:
        return None
    if delta_cp < 100:
        return "inaccuracy"
    if delta_cp < 300:
        return "mistake"
    return "blunder"


def extract_eval_fields(
    infos: list[chess.engine.InfoDict],
    user_color: chess.Color,
) -> dict:
    """Pull the key fields out of a MultiPV analyse result."""
    if not infos:
        return {}

    primary = infos[0]
    score = primary.get("score")
    pv = primary.get("pv", [])

    best_cp: Optional[int] = None
    mate_in: Optional[int] = None
    best_line = " ".join(m.uci() for m in pv[:12]) if pv else ""
    best_move = pv[0].uci() if pv else ""

    if score:
        rel = score.pov(user_color)
        if rel.is_mate():
            mate_in = rel.mate()
        else:
            raw = rel.score()
            best_cp = max(-MATE_CP_BASE, min(MATE_CP_BASE, raw if raw is not None else 0))

    result = {
        "best_move": best_move,
        "best_line": best_line,
        "eval_cp": best_cp,
        "mate_in": mate_in,
    }

    if len(infos) > 1:
        secondary = infos[1]
        sec_score = secondary.get("score")
        sec_pv = secondary.get("pv", [])
        sec_cp: Optional[int] = None
        sec_mate: Optional[int] = None
        if sec_score:
            rel2 = sec_score.pov(user_color)
            if rel2.is_mate():
                sec_mate = rel2.mate()
            else:
                raw2 = rel2.score()
                sec_cp = max(-MATE_CP_BASE, min(MATE_CP_BASE, raw2 if raw2 is not None else 0))
        result["second_best_move"] = sec_pv[0].uci() if sec_pv else None
        result["second_best_eval_cp"] = sec_cp
        result["second_best_mate_in"] = sec_mate

    return result
