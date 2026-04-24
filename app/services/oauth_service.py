"""
services/oauth_service.py - OAuth2 authorization code flow logic
"""
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.auth_code import AuthCode
from app.models.application import Application
from app.services.auth_service import authenticate_user
from app.core.security import create_access_token


def get_app_and_validate_redirect(db: Session, app_id: int, redirect_uri: str) -> Application:
    """Validate that app exists and redirect_uri matches registration."""
    app = db.query(Application).filter(Application.id == app_id, Application.is_active == True).first()
    if not app:
        raise HTTPException(status_code=400, detail="Invalid app_id — application not found or inactive.")
    if app.redirect_uri and app.redirect_uri.rstrip("/") != redirect_uri.rstrip("/"):
        raise HTTPException(
            status_code=400,
            detail=f"redirect_uri mismatch. Registered: {app.redirect_uri}"
        )
    return app


def generate_auth_code(db: Session, user_id: int, app_id: int, redirect_uri: str, state: str | None) -> str:
    """Generate a one-time authorization code valid for 5 minutes."""
    code = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    auth_code = AuthCode(
        code=code,
        user_id=user_id,
        app_id=app_id,
        redirect_uri=redirect_uri,
        state=state,
        expires_at=expires
    )
    db.add(auth_code)
    db.commit()
    return code


def exchange_code_for_token(db: Session, code: str, app_id: int, redirect_uri: str, api_key: str) -> dict:
    """Exchange auth code for JWT access token. Code is single-use."""
    record = db.query(AuthCode).filter(AuthCode.code == code).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid authorization code.")
    if record.used:
        raise HTTPException(status_code=400, detail="Authorization code already used.")
    if record.app_id != app_id:
        raise HTTPException(status_code=400, detail="app_id mismatch.")
    if record.redirect_uri.rstrip("/") != redirect_uri.rstrip("/"):
        raise HTTPException(status_code=400, detail="redirect_uri mismatch.")
    
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app or app.api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid application api_key.")

    if datetime.now(timezone.utc) > record.expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Authorization code has expired.")

    # Mark as used
    record.used = True
    db.commit()

    # Phase 14: Get User's perm_version
    from app.models.user import User
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User no longer exists.")

    # Generate JWT with perm_version
    token = create_access_token(data={"sub": str(record.user_id), "perm_version": user.perm_version})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": record.user_id,
        "app_id": app_id
    }
