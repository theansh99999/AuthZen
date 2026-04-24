"""
services/audit_service.py - Audit log management (Phase 7)

TODO: Implement
  - log_action(db, user_id, action, ip, meta)
  - get_all_logs(db)
  - get_user_logs(db, user_id)
"""

from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from fastapi import Request, BackgroundTasks
from app.db.session import SessionLocal

def _insert_log(user_id: int | None, action: str, ip_address: str | None, meta: dict):
    db = SessionLocal()
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            meta=meta
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Error logging audit action: {e}")
    finally:
        db.close()

def log_action_bg(background_tasks: BackgroundTasks, request: Request, user_id: int | None, action: str, meta: dict = None):
    """
    Non-blocking scalable logging function. Extracts IP and User-Agent safely.
    """
    meta = meta or {}
    ip_address = request.client.host if request and request.client else None
    
    if request:
        user_agent = request.headers.get("user-agent")
        if user_agent:
            meta["user_agent"] = user_agent

    # Strip sensitive data
    for sensitive_key in ["password", "token", "access_token", "refresh_token", "secret"]:
        if sensitive_key in meta:
            meta[sensitive_key] = "***REDACTED***"

    background_tasks.add_task(_insert_log, user_id, action, ip_address, meta)


# Keeping synchronous log_action for backwards compatibility if needed during refactoring
def log_action(db: Session, user_id: int | None, action: str, ip_address: str | None = None, meta: dict = None):
    meta = meta or {}
    for sensitive_key in ["password", "token", "access_token", "refresh_token", "secret"]:
        if sensitive_key in meta:
            meta[sensitive_key] = "***REDACTED***"
            
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        meta=meta
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_logs(db: Session, skip: int = 0, limit: int = 50, action: str | None = None) -> list[AuditLog]:
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

def get_user_logs(db: Session, user_id: int, skip: int = 0, limit: int = 50, action: str | None = None) -> list[AuditLog]:
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
