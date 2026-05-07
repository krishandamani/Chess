from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import get_pool
from app.models.schemas import ProfileResponse

router = APIRouter()


@router.get("/api/me", response_model=ProfileResponse)
async def get_me(user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM profiles WHERE id = $1",
            user["id"],
        )
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return dict(row)
