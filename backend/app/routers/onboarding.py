from celery import Celery
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.database import get_pool
from app.models.schemas import OnboardingRequest, OnboardingResponse

router = APIRouter()

_celery = Celery(broker=settings.redis_url, backend=settings.redis_url)


@router.post("/api/onboarding", response_model=OnboardingResponse)
async def onboarding(body: OnboardingRequest):
    if not body.chesscom_username and not body.lichess_username:
        raise HTTPException(status_code=422, detail="At least one chess username is required")

    pool = await get_pool()
    async with pool.acquire() as conn:
        user_id: str = await conn.fetchval(
            """
            INSERT INTO users (email)
            VALUES ($1)
            ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
            RETURNING id::text
            """,
            body.email,
        )

        await conn.execute(
            """
            UPDATE users
            SET chesscom_username = COALESCE($2, chesscom_username),
                lichess_username  = COALESCE($3, lichess_username)
            WHERE id = $1::uuid
            """,
            user_id,
            body.chesscom_username,
            body.lichess_username,
        )

        job_id: str = await conn.fetchval(
            """
            INSERT INTO analysis_jobs (user_id, kind, status)
            VALUES ($1::uuid, 'initial_recent', 'queued')
            RETURNING id::text
            """,
            user_id,
        )

    _celery.send_task(
        "tasks.ingest.fetch_and_analyze",
        kwargs={"user_id": user_id, "job_id": job_id, "kind": "initial_recent"},
    )

    return OnboardingResponse(user_id=user_id, job_id=job_id)
