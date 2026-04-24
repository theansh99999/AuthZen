"""
services/permission_service.py - Permission management business logic
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate


def create_permission(db: Session, data: PermissionCreate) -> Permission:
    existing = db.query(Permission).filter(
        Permission.name == data.name,
        Permission.app_id == data.app_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Permission '{data.name}' already exists in this scope.")
    perm = Permission(name=data.name, description=data.description, app_id=data.app_id)
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


def get_all_permissions(db: Session, app_id: int | None = None) -> list[Permission]:
    query = db.query(Permission)
    if app_id is not None:
        query = query.filter(Permission.app_id == app_id)
    return query.all()


def get_permission_by_id(db: Session, permission_id: int) -> Permission:
    perm = db.query(Permission).filter(Permission.id == permission_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found.")
    return perm


def delete_permission(db: Session, permission_id: int) -> None:
    perm = get_permission_by_id(db, permission_id)
    db.delete(perm)
    db.commit()
