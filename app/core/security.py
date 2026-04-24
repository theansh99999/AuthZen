"""
security.py - Password hashing aur JWT token utilities

Functions:
  - hash_password(plain)           → hashed string
  - verify_password(plain, hashed) → bool
  - create_access_token(data)      → JWT string
  - decode_access_token(token)     → payload dict
"""

import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings


def _to_bytes(password: str) -> bytes:
    """Password ko UTF-8 bytes me convert karo, 72 bytes tak truncate karo."""
    return password.encode("utf-8")[:72]


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(_to_bytes(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_to_bytes(plain_password), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expires})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expires = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload.update({"exp": expires, "type": "refresh"})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
