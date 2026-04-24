"""
routes/oauth.py - OAuth2 Authorization Code Flow

GET  /authorize?app_id=X&redirect_uri=Y&state=Z  → Show login form
POST /authorize                                    → Authenticate + redirect with code
POST /token                                        → Exchange code for JWT
"""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.auth_service import authenticate_user
from app.services.oauth_service import (
    get_app_and_validate_redirect,
    generate_auth_code,
    exchange_code_for_token,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ── GET /authorize ─────────────────────────────────────────────
@router.get("/authorize", response_class=HTMLResponse)
def authorize_page(
    request: Request,
    app_id: int,
    redirect_uri: str,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    """Show login form with app context. Validates app_id and redirect_uri first."""
    try:
        app = get_app_and_validate_redirect(db, app_id, redirect_uri)
    except Exception as e:
        return templates.TemplateResponse(request, "authorize.html", {
            "error": str(e.detail if hasattr(e, 'detail') else e),
            "app": None, "app_id": app_id, "redirect_uri": redirect_uri, "state": state
        })
    return templates.TemplateResponse(request, "authorize.html", {
        "app": app, "app_id": app_id, "redirect_uri": redirect_uri, "state": state, "error": None
    })


# ── POST /authorize ────────────────────────────────────────────
@router.post("/authorize", response_class=HTMLResponse)
def authorize_submit(
    request: Request,
    app_id: int = Form(...),
    redirect_uri: str = Form(...),
    state: str | None = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Authenticate user, generate auth code, redirect to redirect_uri?code=XXX."""
    try:
        app = get_app_and_validate_redirect(db, app_id, redirect_uri)
    except Exception as e:
        return templates.TemplateResponse(request, "authorize.html", {
            "error": str(e.detail if hasattr(e, 'detail') else e),
            "app": None, "app_id": app_id, "redirect_uri": redirect_uri, "state": state
        })

    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(request, "authorize.html", {
            "error": "Invalid email or password.",
            "app": app, "app_id": app_id, "redirect_uri": redirect_uri, "state": state
        })

    code = generate_auth_code(db, user.id, app_id, redirect_uri, state)

    # Build redirect URL
    sep = "&" if "?" in redirect_uri else "?"
    redirect_url = f"{redirect_uri}{sep}code={code}"
    if state:
        redirect_url += f"&state={state}"

    return RedirectResponse(url=redirect_url, status_code=302)


# ── POST /token ────────────────────────────────────────────────
class TokenRequest(BaseModel):
    code: str
    app_id: int
    redirect_uri: str
    api_key: str

@router.post("/token")
def token_exchange(data: TokenRequest, db: Session = Depends(get_db)):
    """Exchange authorization code for JWT access token. Single-use, 5-minute expiry."""
    return exchange_code_for_token(db, data.code, data.app_id, data.redirect_uri, data.api_key)
