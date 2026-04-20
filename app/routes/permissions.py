"""
routes/permissions.py - Permission management API endpoints

GET  /permissions/     → list all permissions
POST /permissions/     → create permission  [requires: write]
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_permission, get_current_user
from app.schemas.permission import PermissionCreate, PermissionOut
from app.services.permission_service import create_permission, get_all_permissions

router = APIRouter()


@router.get("/", response_model=list[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return get_all_permissions(db)


@router.post("/", response_model=PermissionOut, status_code=201)
def create_new_permission(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("write")),
):
    return create_permission(db, data)
