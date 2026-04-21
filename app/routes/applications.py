"""
routes/applications.py - Application management endpoints (Phase 4: Multi-App)

POST /apps/        → create application
GET  /apps/        → list applications
GET  /apps/{id}    → get application
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import require_permission, get_current_user
from app.schemas.application import ApplicationCreate, ApplicationOut
from app.services.application_service import (
    create_application, 
    get_all_applications, 
    assign_role_to_user_for_app
)

router = APIRouter()


@router.post("/", response_model=ApplicationOut, status_code=201)
def create_app(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("write"))
):
    """Creates a new application configuration."""
    return create_application(db, data)


@router.get("/", response_model=list[ApplicationOut])
def list_apps(
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Lists all active applications."""
    return get_all_applications(db)


@router.post("/{app_id}/users/{user_id}/roles/{role_id}", status_code=200)
def assign_role_to_user_under_app(
    app_id: int,
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("write"))
):
    """Assigns a role strictly to a user under the scope of an application."""
    return assign_role_to_user_for_app(db, user_id, role_id, app_id)
