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
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import register_user, authenticate_user
from app.core.security import create_access_token, decode_access_token
from app.services.user_service import get_user_by_id
from app.core.config import settings

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

    # Generate JWT with user_id in payload
    token = create_access_token(data={"sub": str(user.id)})

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


# ─── Dashboard (Protected) ───────────────────────────────────
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
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

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "token": token,
            "expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        },
    )


# ─── Logout ──────────────────────────────────────────────────
@router.get("/logout", response_class=RedirectResponse)
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
