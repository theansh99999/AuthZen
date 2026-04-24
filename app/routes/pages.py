"""
routes/pages.py - Jinja2 HTML page routes (web UI)

Flow:
  GET  /         → redirect to /login
  GET  /signup   → render signup.html
  POST /signup   → register user, redirect to /login
  GET  /login    → render login.html
  POST /login    → verify creds, set JWT cookie, redirect to /dashboard
  GET  /dashboard → protected, render dashboard.html
  GET  /logout   → clear cookie, redirect to /login
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload
from pydantic import ValidationError

from app.db.session import get_db
from app.schemas.user import UserCreate
from app.services.auth_service import register_user, authenticate_user
from app.core.security import create_access_token, decode_access_token
from app.services.user_service import get_user_by_id
from app.core.config import settings
from app.models.user import User
from app.models.role import Role

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ─── Home ────────────────────────────────────────────────────
@router.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse(url="/login", status_code=302)


# ─── Signup ──────────────────────────────────────────────────
@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {})


@router.post("/signup", response_class=HTMLResponse)
def signup_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if len(password) < 6:
        return templates.TemplateResponse(
            request,
            "signup.html",
            {
                "error": "Password must be at least 6 characters.",
                "form_data": {"username": username, "email": email},
            },
        )
    try:
        data = UserCreate(username=username, email=email, password=password)
        register_user(db, data)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"success": "Account created! Please sign in."},
        )
    except ValidationError as e:
        # Pydantic validation error (e.g. invalid email format)
        errors = e.errors()
        msg = errors[0]["msg"] if errors else "Invalid input."
        return templates.TemplateResponse(
            request,
            "signup.html",
            {
                "error": msg,
                "form_data": {"username": username, "email": email},
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "signup.html",
            {
                "error": str(e.detail) if hasattr(e, "detail") else str(e),
                "form_data": {"username": username, "email": email},
            },
        )


# ─── Login ───────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    # Already logged in? → dashboard
    token = request.cookies.get("access_token")
    if token and decode_access_token(token):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid email or password."},
        )

    # Generate JWT with user_id and perm_version in payload
    token = create_access_token(data={"sub": str(user.id), "perm_version": user.perm_version})

    # Set as HttpOnly cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


import secrets
from app.models.permission import Permission
from app.models.application import Application

# ─── Dashboard (Protected) ───────────────────────────────────
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, app_id: int | None = None, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(url="/login", status_code=302)

    payload = decode_access_token(token)
    if not payload:
        response = RedirectResponse(url="/login", status_code=302)
        response.delete_cookie("access_token")
        return response

    user_id = int(payload.get("sub"))
    user = get_user_by_id(db, user_id)

    # Admin Check
    is_admin = any(role.name == "admin" for role in user.roles)
    if not is_admin:
        # Phase 13: Regular users see their accessible apps
        from app.services.iam_service import get_user_accessible_apps
        user_apps = get_user_accessible_apps(db, user)
        return templates.TemplateResponse(
            request,
            "user_dashboard.html",
            {
                "user": user,
                "user_apps": user_apps,
            }
        )

    # Fetch context data
    all_apps_query = db.query(Application)
    all_roles_query = db.query(Role).options(selectinload(Role.permissions))
    all_permissions_query = db.query(Permission)
    
    if app_id:
        all_roles_query = all_roles_query.filter(Role.app_id == app_id)
        all_permissions_query = all_permissions_query.filter(Permission.app_id == app_id)

    all_users = db.query(User).options(selectinload(User.roles).selectinload(Role.permissions)).all()
    all_roles = all_roles_query.all()
    all_permissions = all_permissions_query.all()
    all_apps = all_apps_query.all()

    # Generate CSRF token
    csrf_token = request.cookies.get("csrf_token") or secrets.token_hex(32)

    response = templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "token": token,
            "csrf_token": csrf_token,
            "expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "all_users": all_users,
            "all_roles": all_roles,
            "all_permissions": all_permissions,
            "all_apps": all_apps,
            "selected_app_id": app_id,
        },
    )
    
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False, # Must be readable by JS to send in header, or we embed in HTML. Better to set httponly=False so JS can read it, or set in HTML and keep cookie httponly. 
        # Actually, standard practice for CSRF: cookie is NOT HttpOnly so JS can read it and send in header, OR embed in meta tag and keep cookie HttpOnly. Let's embed in HTML to be safer, and keep cookie HttpOnly.
        max_age=3600,
        samesite="lax",
    )
    return response


# ─── Logout ──────────────────────────────────────────────────
@router.get("/logout", response_class=RedirectResponse)
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

