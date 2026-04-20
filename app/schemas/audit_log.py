"""
schemas/audit_log.py - Pydantic schemas for Audit Log (Phase 7)
"""

from pydantic import BaseModel
from datetime import datetime


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    ip_address: str | None
    meta: dict | None
    timestamp: datetime

    model_config = {"from_attributes": True}
