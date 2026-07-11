from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.security import decode_token

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Verify our access token and confirm it has not been revoked.

    Rejects the token if its `ver` claim no longer matches the user's
    `token_version` (which is bumped on password change/reset).
    """
    from app.models.core import User

    try:
        payload = decode_token(credentials.credentials, "access")
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing subject")

    user = await db.get(User, sub)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    if payload.get("ver") != user.token_version:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    return UUID(sub)


async def require_school_admin(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    from app.models.core import UserRole
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == str(user_id),
            UserRole.role.in_(["school_admin", "super_admin"]),
        )
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="School admin access required")
    return user_id


async def require_teacher(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    from app.models.academic import Teacher
    result = await db.execute(
        select(Teacher).where(Teacher.profile_id == str(user_id))
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Teacher access required")
    return user_id
