"""
routes/applications.py - Application management endpoints (Phase 4: Multi-App)

POST /apps/        → create application
GET  /apps/        → list applications
GET  /apps/{id}    → get application
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.core.dependencies import require_permission, get_current_user, verify_csrf_token
from app.schemas.application import ApplicationCreate, ApplicationOut
from app.services.application_service import (
    create_application, 
    get_all_applications, 
    assign_role_to_user_for_app
)
from app.services.audit_service import log_action

router = APIRouter()


@router.post("/", response_model=ApplicationOut, status_code=201, dependencies=[Depends(verify_csrf_token)])
def create_app(
    data: ApplicationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write"))
):
    """Creates a new application configuration."""
    try:
        app = create_application(db, data)
        log_action(db, current_user.id, "create_application", request.client.host, {"app_name": app.name})
        return app
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application with this name already exists.")


@router.get("/", response_model=list[ApplicationOut])
def list_apps(
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Lists all active applications."""
    return get_all_applications(db)


@router.post("/{app_id}/users/{user_id}/roles/{role_id}", status_code=200, dependencies=[Depends(verify_csrf_token)])
def assign_role_to_user_under_app(
    app_id: int,
    user_id: int,
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write"))
):
    """Assigns a role strictly to a user under the scope of an application."""
    res = assign_role_to_user_for_app(db, user_id, role_id, app_id)
    log_action(db, current_user.id, "assign_role_for_app", request.client.host, {"user_id": user_id, "role_id": role_id, "app_id": app_id})
    return res
