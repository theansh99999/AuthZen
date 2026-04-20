"""
services/user_service.py - User management business logic

Functions:
  - get_user_by_id(db, user_id) → User | None
  - get_all_users(db)           → list[User]
  - deactivate_user(db, user_id) → User
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_all_users(db: Session) -> list[User]:
    return db.query(User).all()


def deactivate_user(db: Session, user_id: int) -> User:
    user = get_user_by_id(db, user_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
