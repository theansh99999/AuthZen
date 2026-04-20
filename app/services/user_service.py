"""
services/user_service.py - User management business logic
"""

from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException
from app.models.user import User
from app.models.role import Role


def get_user_by_id(db: Session, user_id: int) -> User:
    user = (
        db.query(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_all_users(db: Session) -> list[User]:
    return (
        db.query(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .all()
    )


def deactivate_user(db: Session, user_id: int) -> User:
    user = get_user_by_id(db, user_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
