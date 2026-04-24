"""
routes/permissions.py - Permission management API endpoints

GET  /permissions/     → list all permissions
POST /permissions/     → create permission  [requires: write]
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.core.dependencies import require_permission, get_current_user, verify_csrf_token
from app.schemas.permission import PermissionCreate, PermissionOut
from app.services.permission_service import create_permission, get_all_permissions
from app.services.audit_service import log_action

router = APIRouter()


@router.get("/", response_model=list[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return get_all_permissions(db)


@router.post("/", response_model=PermissionOut, status_code=201, dependencies=[Depends(verify_csrf_token)])
def create_new_permission(
    data: PermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write")),
):
    try:
        perm = create_permission(db, data)
        log_action(db, current_user.id, "create_permission", request.client.host, {"permission_name": perm.name, "app_id": perm.app_id})
        return perm
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Permission with this name already exists in the application scope.")
