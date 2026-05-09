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
        # Find existing user by chess username (allows recovery if localStorage cleared)
        user_id: str | None = None
        if body.chesscom_username:
            user_id = await conn.fetchval(
                "SELECT id::text FROM users WHERE chesscom_username = $1",
                body.chesscom_username,
            )
        if not user_id and body.lichess_username:
            user_id = await conn.fetchval(
                "SELECT id::text FROM users WHERE lichess_username = $1",
                body.lichess_username,
            )

        if user_id:
            # Update usernames in case they added the other platform
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
        else:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (chesscom_username, lichess_username)
                VALUES ($1, $2)
                RETURNING id::text
                """,
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
