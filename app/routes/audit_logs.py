"""
routes/audit_logs.py - Audit log endpoints (Phase 7)

GET /logs/          → all logs (admin)
GET /logs/me        → current user's logs
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.schemas.audit_log import AuditLogOut
from app.services.audit_service import get_logs, get_user_logs
from typing import List

router = APIRouter()

@router.get("/", response_model=List[AuditLogOut])
def get_all_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """Admin only: Fetch all audit logs across the system with pagination and filtering."""
    return get_logs(db, skip=skip, limit=limit, action=action)


@router.get("/me", response_model=List[AuditLogOut])
def get_my_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Fetch audit logs strictly for the currently authenticated user."""
    return get_user_logs(db, user_id=current_user.id, skip=skip, limit=limit, action=action)
