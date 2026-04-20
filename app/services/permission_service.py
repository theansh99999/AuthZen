"""
services/permission_service.py - Permission management business logic
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate


def create_permission(db: Session, data: PermissionCreate) -> Permission:
    if db.query(Permission).filter(Permission.name == data.name).first():
        raise HTTPException(status_code=400, detail=f"Permission '{data.name}' already exists.")
    perm = Permission(name=data.name, description=data.description)
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


def get_all_permissions(db: Session) -> list[Permission]:
    return db.query(Permission).all()


def get_permission_by_id(db: Session, permission_id: int) -> Permission:
    perm = db.query(Permission).filter(Permission.id == permission_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found.")
    return perm
