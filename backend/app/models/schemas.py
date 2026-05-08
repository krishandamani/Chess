from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


# ── Onboarding ─────────────────────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    email: str
    chesscom_username: Optional[str] = None
    lichess_username: Optional[str] = None

    @field_validator("chesscom_username", "lichess_username", mode="before")
    @classmethod
    def strip_and_lower(cls, v: str | None) -> str | None:
        return v.strip().lower() if v else None


class OnboardingResponse(BaseModel):
    user_id: str
    job_id: str


# ── User profile ───────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    chesscom_username: Optional[str]
    lichess_username: Optional[str]
    subscription_status: str
    trial_ends_at: Optional[datetime]
    timezone: str
    created_at: datetime


# ── Analysis job ───────────────────────────────────────────────────────────────

class JobStatusResponse(BaseModel):
    id: str
    kind: str
    status: str
    games_total: int
    games_done: int
    positions_analyzed: int
    cache_hits: int
    error: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime


# ── Ingest trigger ─────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    user_id: str
    days: int = 30


# ── Error (RFC 7807) ────────────────────────────────────────────────────────────

class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
