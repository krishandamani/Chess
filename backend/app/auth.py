"""NextAuth JWT verification for FastAPI.

NextAuth v5 issues HS256 JWTs signed with NEXTAUTH_SECRET.
The token is passed as a Bearer token from the frontend API client.
We verify it here and extract the user's email (used to look up our users table).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.config import settings

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.nextauth_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    # NextAuth encodes the user's email in the token; we use it to find our users row
    email: str | None = payload.get("email")
    user_id: str | None = payload.get("sub")
    if not email and not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing identity")

    return {"email": email, "sub": user_id}
