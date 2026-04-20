"""
schemas/role.py - Pydantic schemas for Role (Phase 2: RBAC)

RoleCreate → create role request
RoleOut    → role response
"""

from pydantic import BaseModel
from datetime import datetime


class RoleCreate(BaseModel):
    name: str
    description: str | None = None


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
