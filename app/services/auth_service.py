"""
services/auth_service.py - Authentication business logic

Functions:
  - register_user(db, data)  → User
  - authenticate_user(db, email, password) → User | None
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def register_user(db: Session, data: UserCreate) -> User:
    # Check duplicate email/username
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


from datetime import datetime, timedelta, timezone
from app.core.config import settings

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Account is locked due to multiple failed login attempts. Try again later.")

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
        db.commit()
        return None

    # Reset on success
    user.failed_login_attempts = 0
    user.account_locked_until = None
    db.commit()

    return user
