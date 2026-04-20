"""
models/audit_log.py - Audit Log ORM Model (Phase 7: Audit Logs)

Table: audit_logs
Columns: id, user_id, action, ip_address, metadata, timestamp

Tracks: login attempts, role changes, permission checks
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)        # e.g. "login", "role_assigned"
    ip_address = Column(String(50), nullable=True)
    meta = Column(JSON, nullable=True)                  # extra context
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
