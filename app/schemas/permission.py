"""
schemas/permission.py - Pydantic schemas for Permission (Phase 2: RBAC)
"""

from pydantic import BaseModel
from datetime import datetime


class PermissionCreate(BaseModel):
    name: str
    description: str | None = None


class PermissionOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
