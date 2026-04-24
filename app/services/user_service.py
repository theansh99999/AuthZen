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


def delete_user(db: Session, user_id: int) -> None:
    user = get_user_by_id(db, user_id)
    
    # Check if admin is trying to delete themselves
    has_admin_role = any(r.name == "admin" for r in user.roles)
    if has_admin_role:
        # Check if they are the only admin left
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role and len(admin_role.users) <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin user.")

    # Fix foreign key constraint: Nullify user_id in audit_logs before deletion
    from sqlalchemy import text
    db.execute(text("UPDATE audit_logs SET user_id = NULL WHERE user_id = :uid"), {"uid": user_id})

    db.delete(user)
    db.commit()
