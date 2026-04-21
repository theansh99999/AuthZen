"""
services/role_service.py - Role management business logic
"""

from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.schemas.role import RoleCreate


def create_role(db: Session, data: RoleCreate) -> Role:
    if db.query(Role).filter(Role.name == data.name, Role.app_id == data.app_id).first():
        raise HTTPException(status_code=400, detail=f"Role '{data.name}' already exists in this scope.")
    role = Role(name=data.name, description=data.description, app_id=data.app_id)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def get_all_roles(db: Session) -> list[Role]:
    return db.query(Role).options(selectinload(Role.permissions)).all()


def get_role_by_id(db: Session, role_id: int) -> Role:
    role = db.query(Role).options(selectinload(Role.permissions)).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")
    return role


def assign_permission_to_role(db: Session, role_id: int, permission_id: int) -> Role:
    role = get_role_by_id(db, role_id)
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found.")
    
    if role.app_id is not None and permission.app_id is not None:
        if role.app_id != permission.app_id:
            raise HTTPException(status_code=400, detail="Role and Permission must belong to the same application.")
            
    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()
    db.refresh(role)
    return role


def remove_permission_from_role(db: Session, role_id: int, permission_id: int) -> Role:
    role = get_role_by_id(db, role_id)
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if permission and permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()
    db.refresh(role)
    return role


def assign_role_to_user(db: Session, user_id: int, role_id: int) -> User:
    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
    db.refresh(user)
    return user


def get_user_roles(db: Session, user_id: int) -> list[Role]:
    user = db.query(User).options(
        selectinload(User.roles).selectinload(Role.permissions)
    ).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user.roles
