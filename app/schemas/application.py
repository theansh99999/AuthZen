"""
schemas/application.py - Pydantic schemas for Application (Phase 4: Multi-App)
"""

from pydantic import BaseModel
from datetime import datetime


class ApplicationCreate(BaseModel):
    name: str
    description: str | None = None


class ApplicationOut(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
