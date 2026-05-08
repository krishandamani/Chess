from celery import Celery
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.database import get_pool
from app.models.schemas import IngestRequest, JobStatusResponse, OnboardingResponse

router = APIRouter()

_celery = Celery(broker=settings.redis_url, backend=settings.redis_url)


@router.post("/api/ingest", response_model=OnboardingResponse)
async def trigger_ingest(body: IngestRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT id FROM users WHERE id = $1::uuid",
            body.user_id,
        )
        if not exists:
            raise HTTPException(status_code=404, detail="User not found")

        job_id: str = await conn.fetchval(
            """
            INSERT INTO analysis_jobs (user_id, kind, status)
            VALUES ($1::uuid, 'incremental', 'queued')
            RETURNING id::text
            """,
            body.user_id,
        )

    _celery.send_task(
        "tasks.ingest.fetch_and_analyze",
        kwargs={"user_id": body.user_id, "job_id": job_id, "kind": "incremental", "days": body.days},
    )

    return OnboardingResponse(user_id=body.user_id, job_id=job_id)


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, user_id: str = Query(...)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM analysis_jobs WHERE id = $1::uuid AND user_id = $2::uuid",
            job_id,
            user_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(row)
