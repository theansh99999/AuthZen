"""
core/dependencies.py - Reusable FastAPI dependencies

get_current_user:
    Bearer token extract → decode JWT → DB se User fetch → return User object

require_permission(permission_name):
    Factory function — returns a dependency that checks if user has the given permission.
    Usage:
        @router.post("/article")
        def create(user = Depends(require_permission("write"))):
            ...
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.role import Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Works for both:
      - API calls  → Authorization: Bearer <token>
      - Web calls  → access_token cookie
    """
    # Try Bearer token first, then cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub"))

    # Eager load roles + permissions in single query
    user = (
        db.query(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .filter(User.id == user_id)
        .first()
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    return user


def require_permission(permission_name: str):
    """
    Dependency factory — permission-based access control.

    Example:
        Depends(require_permission("write"))
        Depends(require_permission("delete"))
    """
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = {
            perm.name
            for role in current_user.roles
            for perm in role.permissions
        }
        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required.",
            )
        return current_user

    return dependency
