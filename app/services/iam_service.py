"""
services/iam_service.py - Reusable IAM Component

Contains reusable logic for extracting and validating a user from a token,
and checking their permissions across granular roles/applications.
"""

from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status
from app.core.security import decode_access_token
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission


def verify_jwt_token(db: Session, token: str) -> User | None:
    """
    Decodes the JWT token and fetches the User from the database.
    Also eager loads their roles and permissions to be used later.
    """
    payload = decode_access_token(token)
    if not payload:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = int(user_id_str)
    except ValueError:
        return None

    # We use selectinload to eagerly load the roles and permissions 
    # to avoid lazy loading issues later in the session lifecycle.
    user = (
        db.query(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .filter(User.id == user_id)
        .first()
    )

    if not user or not user.is_active:
        return None

    # Phase 14: Stale token invalidation
    token_perm_version = payload.get("perm_version", 1)
    if token_perm_version != user.perm_version:
        return None

    return user


def check_user_permission(db: Session, user: User, permission_name: str, app_id: int | None = None) -> bool:
    """
    Validates if the user has the required permission.
    If app_id is provided, checks if the user has the permission specifically 
    granted to that application, or via a global role.
    """
    if app_id is not None:
        # Phase 4 Many to Many schema query
        # Since we added app_id in the user_roles table, we need to query explicitly 
        # to see which roles the user has for this app_id or global (app_id IS NULL)
        from app.models.associations import user_roles
        
        # Get roles that match the user and (to the app or global)
        stmt = (
            db.query(Role)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .filter(
                user_roles.c.user_id == user.id,
                (user_roles.c.app_id == app_id) | (user_roles.c.app_id.is_(None))
            )
        )
        active_roles = stmt.all()
    else:
        # standard global evaluation
        active_roles = user.roles

    for role in active_roles:
        for perm in role.permissions:
            if perm.name == permission_name:
                return True
                
    return False

def has_app_access(db: Session, user: User, app_id: int) -> bool:
    """
    Checks if a user has at least one role assigned for the specific app_id,
    OR if the user has a global role (app_id IS NULL) which implicitly grants access.
    """
    from app.models.associations import user_roles
    
    # Check for any role mapping matching this user and this app (or global)
    stmt = (
        db.query(user_roles)
        .filter(
            user_roles.c.user_id == user.id,
            (user_roles.c.app_id == app_id) | (user_roles.c.app_id.is_(None))
        )
    )
    mapping = stmt.first()
    return mapping is not None

def get_user_accessible_apps(db: Session, user: User) -> list:
    """
    Returns a list of Application objects that the user has access to.
    If the user has a global role, they get access to all active apps.
    Otherwise, they only get apps explicitly mapped to them.
    """
    from app.models.application import Application
    from app.models.associations import user_roles
    
    # Check if user has any global role
    global_role_stmt = (
        db.query(user_roles)
        .filter(
            user_roles.c.user_id == user.id,
            user_roles.c.app_id.is_(None)
        )
    )
    has_global = global_role_stmt.first() is not None
    
    if has_global:
        return db.query(Application).filter(Application.is_active == True).all()
        
    # User only has app-specific roles
    stmt = (
        db.query(Application)
        .join(user_roles, user_roles.c.app_id == Application.id)
        .filter(
            user_roles.c.user_id == user.id,
            Application.is_active == True
        )
        .distinct()
    )
    return stmt.all()
