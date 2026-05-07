from fastapi import APIRouter, Response
import asyncpg
import redis.asyncio as aioredis

from app.config import settings
from app.database import get_pool

router = APIRouter()


@router.get("/api/health")
async def health(response: Response):
    result: dict[str, str] = {"status": "ok"}

    # Database check
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        result["db"] = "ok"
    except Exception as exc:
        result["db"] = f"error: {exc}"
        result["status"] = "degraded"

    # Redis check
    try:
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        result["redis"] = "ok"
    except Exception as exc:
        result["redis"] = f"error: {exc}"
        result["status"] = "degraded"

    if result["status"] != "ok":
        response.status_code = 503
    return result
