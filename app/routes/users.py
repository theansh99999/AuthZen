"""
routes/users.py - User management API endpoints (protected)

GET  /users/                     → list all users
GET  /users/me                   → current user profile
GET  /users/me/permissions       → current user's permissions (flat list)
GET  /users/{user_id}            → get user by id
POST /users/{user_id}/roles/{role_id}   → assign role to user [requires: write]
DELETE /users/{user_id}/roles/{role_id} → remove role from user [requires: delete]
GET  /users/{user_id}/roles      → get user's roles
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_permission
from app.schemas.user import UserOut
from app.schemas.role import RoleOut
from app.schemas.permission import PermissionOut
from app.services.user_service import get_user_by_id, get_all_users
from app.services.role_service import assign_role_to_user, get_user_roles
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/permissions", response_model=list[PermissionOut])
def get_my_permissions(current_user: User = Depends(get_current_user)):
    """Current user ke saare permissions (flat list, no duplicates)."""
    seen = set()
    permissions = []
    for role in current_user.roles:
        for perm in role.permissions:
            if perm.id not in seen:
                seen.add(perm.id)
                permissions.append(perm)
    return permissions


@router.get("/", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("read")),
):
    return get_all_users(db)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_user_by_id(db, user_id)


@router.get("/{user_id}/roles", response_model=list[RoleOut])
def get_roles_of_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_user_roles(db, user_id)


@router.post("/{user_id}/roles/{role_id}", response_model=UserOut)
def assign_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("write")),
):
    return assign_role_to_user(db, user_id, role_id)
