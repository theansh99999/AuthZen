"""
routes/roles.py - Role management API endpoints

GET  /roles/                              → list all roles
POST /roles/                              → create role        [requires: write]
POST /roles/{role_id}/permissions/{perm_id} → assign permission to role [requires: write]
DELETE /roles/{role_id}/permissions/{perm_id} → remove permission from role [requires: delete]
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_permission, get_current_user
from app.schemas.role import RoleCreate, RoleOut
from app.services.role_service import (
    create_role, get_all_roles, get_role_by_id,
    assign_permission_to_role, remove_permission_from_role,
)

router = APIRouter()


@router.get("/", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return get_all_roles(db)


@router.post("/", response_model=RoleOut, status_code=201)
def create_new_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("write")),
):
    return create_role(db, data)


@router.post("/{role_id}/permissions/{permission_id}", response_model=RoleOut)
def assign_perm_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("write")),
):
    return assign_permission_to_role(db, role_id, permission_id)


@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleOut)
def remove_perm_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("delete")),
):
    return remove_permission_from_role(db, role_id, permission_id)
