"""Pure auth helpers: password hashing and JWT issue/verify.

No FastAPI and no DB here — everything in this module is unit-testable in
isolation. FastAPI request wiring lives in app/auth.py.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from app.config import settings

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    # bcrypt silently truncates input beyond 72 bytes; fine for our use.
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(sub: str, token_version: int, token_type: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(sub),
        "ver": token_version,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_access_token(user_id: str, token_version: int) -> str:
    return _create_token(
        user_id, token_version, "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str, token_version: int) -> str:
    return _create_token(
        user_id, token_version, "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise JWTError(f"Expected a {expected_type} token")
    return payload


def generate_reset_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Send raw to the user, store only the hash."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_reset_token(raw)


def hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
