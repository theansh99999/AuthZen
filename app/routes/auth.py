"""
routes/auth.py - Authentication endpoints

POST /auth/signup  → register new user
POST /auth/login   → login, get JWT token
"""

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut, Token, RefreshTokenRequest
from app.models.user import User
from app.services.auth_service import register_user, authenticate_user
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.utils.rate_limit import rate_limiter
from fastapi import HTTPException, status
from app.services.audit_service import log_action_bg

router = APIRouter()


@router.post("/signup", response_model=UserOut, status_code=201, dependencies=[Depends(rate_limiter)])
def signup(data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, data)
    return user


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limiter)])
def login(data: UserLogin, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        usr = db.query(User).filter(User.email == data.email).first()
        log_action_bg(background_tasks, request, usr.id if usr else None, "login_failed", {"email": data.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    log_action_bg(background_tasks, request, user.id, "login_success", {"email": user.email})
    access_token = create_access_token(data={"sub": str(user.id), "perm_version": user.perm_version})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "perm_version": user.perm_version})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token, dependencies=[Depends(rate_limiter)])
def refresh(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_refresh_token(data.refresh_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or deleted")

    # Issue a new access token with CURRENT perm_version
    new_access_token = create_access_token(data={"sub": str(user.id), "perm_version": user.perm_version})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id), "perm_version": user.perm_version})
    
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


from app.schemas.iam import TokenValidationRequest, TokenValidationResponse, PermissionCheckRequest, PermissionCheckResponse
from app.services.iam_service import verify_jwt_token, check_user_permission
from app.core.dependencies import verify_api_key, oauth2_scheme

@router.post(
    "/validate-token",
    response_model=TokenValidationResponse,
    dependencies=[Depends(verify_api_key), Depends(rate_limiter)]
)
def validate_token(
    data: TokenValidationRequest,
    header_token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token = data.token or header_token
    if not token:
        return {"is_valid": False, "error": "Token missing"}
        
    user = verify_jwt_token(db, token)
    if not user:
        return {"is_valid": False, "error": "Invalid or expired token"}
        
    return {"is_valid": True, "user": user}


@router.post(
    "/check-permission",
    response_model=PermissionCheckResponse,
    dependencies=[Depends(verify_api_key), Depends(rate_limiter)]
)
def check_permission(
    data: PermissionCheckRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    header_token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token = data.token or header_token
    if not token:
        return {"has_permission": False, "error": "Token missing"}
        
    user = verify_jwt_token(db, token)
    if not user:
        return {"has_permission": False, "error": "Invalid or expired token"}
        
    has_perm = check_user_permission(db, user, data.permission, data.app_id)
    log_action_bg(background_tasks, request, user.id, "permission_check", {
        "permission": data.permission,
        "app_id": data.app_id,
        "granted": has_perm
    })
    return {"has_permission": has_perm}
