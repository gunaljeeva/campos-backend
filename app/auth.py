from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.config import settings
from app.database import get_db

security = HTTPBearer()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")
    return UUID(user_id)


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    return decode_token(credentials.credentials)


async def require_school_admin(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    from app.models.core import UserRole
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
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
        select(Teacher).where(Teacher.profile_id == user_id)
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Teacher access required")
    return user_id
