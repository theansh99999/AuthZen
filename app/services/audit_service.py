"""
services/audit_service.py - Audit log management (Phase 7)

TODO: Implement
  - log_action(db, user_id, action, ip, meta)
  - get_all_logs(db)
  - get_user_logs(db, user_id)
"""

from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from fastapi import Request

def log_action(db: Session, user_id: int | None, action: str, ip_address: str | None = None, meta: dict = None):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        meta=meta or {}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log

def get_all_logs(db: Session) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()

def get_user_logs(db: Session, user_id: int) -> list[AuditLog]:
    return db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).all()
