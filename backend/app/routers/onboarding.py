from celery import Celery
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.config import settings
from app.database import get_pool
from app.models.schemas import OnboardingRequest, OnboardingResponse

router = APIRouter()

# Lightweight Celery client — only used to send tasks, not execute them.
_celery = Celery(broker=settings.redis_url, backend=settings.redis_url)


@router.post("/api/onboarding", response_model=OnboardingResponse)
async def onboarding(body: OnboardingRequest, user: dict = Depends(get_current_user)):
    if not body.chesscom_username and not body.lichess_username:
        raise HTTPException(status_code=422, detail="At least one chess username is required")

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE profiles
            SET chesscom_username = COALESCE($2, chesscom_username),
                lichess_username  = COALESCE($3, lichess_username)
            WHERE id = $1
            """,
            user["id"],
            body.chesscom_username,
            body.lichess_username,
        )

        job_id: str = await conn.fetchval(
            """
            INSERT INTO analysis_jobs (user_id, kind, status)
            VALUES ($1, 'initial_recent', 'queued')
            RETURNING id::text
            """,
            user["id"],
        )

    _celery.send_task(
        "tasks.ingest.fetch_and_analyze",
        kwargs={"user_id": user["id"], "job_id": job_id, "kind": "initial_recent"},
    )

    return OnboardingResponse(job_id=job_id)
