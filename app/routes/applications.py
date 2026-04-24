"""
routes/applications.py - Application management endpoints (Phase 4: Multi-App)

POST /apps/        → create application
GET  /apps/        → list applications
GET  /apps/{id}    → get application
"""

from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.core.dependencies import require_permission, get_current_user, verify_csrf_token, require_admin
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut
from app.services.application_service import (
    create_application,
    get_all_applications,
    get_application_by_id,
    update_application,
    regenerate_api_key,
    delete_application,
    assign_role_to_user_for_app
)
from app.services.audit_service import log_action_bg

router = APIRouter()


@router.post("/", response_model=ApplicationOut, status_code=201, dependencies=[Depends(verify_csrf_token)])
def create_app(
    data: ApplicationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write"))
):
    """Creates a new application with auto-generated API key."""
    try:
        app = create_application(db, data)
        log_action_bg(background_tasks, request, current_user.id, "create_application", {"app_name": app.name})
        return app
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application with this name already exists.")


@router.get("/", response_model=list[ApplicationOut])
def list_apps(
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Lists all registered applications."""
    return get_all_applications(db)


@router.get("/{app_id}", response_model=ApplicationOut)
def get_app(
    app_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """Get a single application by ID (admin only)."""
    return get_application_by_id(db, app_id)


@router.patch("/{app_id}", response_model=ApplicationOut, dependencies=[Depends(verify_csrf_token)])
def update_app(
    app_id: int,
    data: ApplicationUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Update app description, redirect_uri, or active status (admin only)."""
    app = update_application(db, app_id, data)
    log_action_bg(background_tasks, request, current_user.id, "update_application", {"app_id": app_id})
    return app


@router.post("/{app_id}/regenerate-key", response_model=ApplicationOut, dependencies=[Depends(verify_csrf_token)])
def regen_key(
    app_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Regenerate the API key for an application (admin only)."""
    app = regenerate_api_key(db, app_id)
    log_action_bg(background_tasks, request, current_user.id, "regenerate_api_key", {"app_id": app_id})
    return app


@router.delete("/{app_id}", status_code=204, dependencies=[Depends(verify_csrf_token)])
def delete_app(
    app_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Delete an application (admin only)."""
    delete_application(db, app_id)
    log_action_bg(background_tasks, request, current_user.id, "delete_application", {"app_id": app_id})


@router.post("/{app_id}/users/{user_id}/roles/{role_id}", status_code=200, dependencies=[Depends(verify_csrf_token)])
def assign_role_to_user_under_app(
    app_id: int,
    user_id: int,
    role_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("write"))
):
    """Assigns a role to a user within an application scope."""
    res = assign_role_to_user_for_app(db, user_id, role_id, app_id)
    log_action_bg(background_tasks, request, current_user.id, "assign_role_for_app", {"user_id": user_id, "role_id": role_id, "app_id": app_id})
    return res
