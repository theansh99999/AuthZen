"""
routes/roles.py - Role management API endpoints

GET  /roles/                              → list all roles
POST /roles/                              → create role        [requires: write]
POST /roles/{role_id}/permissions/{perm_id} → assign permission to role [requires: write]
DELETE /roles/{role_id}/permissions/{perm_id} → remove permission from role [requires: delete]
"""

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.db.session import get_db
from app.core.dependencies import require_permission, get_current_user, verify_csrf_token
from app.schemas.role import RoleCreate, RoleOut
from app.services.role_service import (
    create_role, get_all_roles, get_role_by_id,
    assign_permission_to_role, remove_permission_from_role, delete_role,
)
from app.services.audit_service import log_action_bg

router = APIRouter()


@router.get("/", response_model=list[RoleOut])
def list_roles(
    app_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return get_all_roles(db, app_id=app_id)


@router.post("/", response_model=RoleOut, status_code=201, dependencies=[Depends(verify_csrf_token)])
def create_new_role(
    data: RoleCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write")),
):
    try:
        role = create_role(db, data)
        log_action_bg(background_tasks, request, current_user.id, "create_role", {"role_name": role.name, "app_id": role.app_id})
        return role
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role with this name already exists in the application scope.")


@router.post("/{role_id}/permissions/{permission_id}", response_model=RoleOut, dependencies=[Depends(verify_csrf_token)])
def assign_perm_to_role(
    role_id: int,
    permission_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write")),
):
    role = assign_permission_to_role(db, role_id, permission_id)
    log_action_bg(background_tasks, request, current_user.id, "assign_permission", {"role_id": role_id, "permission_id": permission_id})
    return role


@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleOut, dependencies=[Depends(verify_csrf_token)])
def remove_perm_from_role(
    role_id: int,
    permission_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("delete")),
):
    role = remove_permission_from_role(db, role_id, permission_id)
    log_action_bg(background_tasks, request, current_user.id, "remove_permission", {"role_id": role_id, "permission_id": permission_id})
    return role


@router.delete("/{role_id}", status_code=204, dependencies=[Depends(verify_csrf_token)])
def delete_role_endpoint(
    role_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("delete")),
):
    delete_role(db, role_id)
    log_action_bg(background_tasks, request, current_user.id, "delete_role", {"role_id": role_id})
