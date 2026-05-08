from fastapi import APIRouter, HTTPException, Query

from app.database import get_pool
from app.models.schemas import ProfileResponse

router = APIRouter()


@router.get("/api/me", response_model=ProfileResponse)
async def get_me(user_id: str = Query(...)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1::uuid",
            user_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)
