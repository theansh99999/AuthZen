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
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.services.iam_service import verify_jwt_token, check_user_permission
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Depends(api_key_header)):
    """External Apps ke liye optional security via API key."""
    if api_key and api_key != settings.IAM_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key for IAM Service",
        )
    return api_key


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
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_jwt_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token, or user inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permission(permission_name: str, app_id: int | None = None):
    """
    Dependency factory — permission-based access control.
    Supports app_id for multi-tenant checks.
    """
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        has_permission = check_user_permission(db, current_user, permission_name, app_id=app_id)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required.",
            )
        return current_user

    return dependency

def require_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    # Basic check: user must have a role named "admin"
    is_admin = any(role.name == "admin" for role in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user

def verify_csrf_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return True

    csrf_token = request.headers.get("x-csrf-token")
    cookie_csrf = request.cookies.get("csrf_token")
    if not csrf_token or not cookie_csrf or csrf_token != cookie_csrf:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token"
        )
    return True
