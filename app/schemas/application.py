from pydantic import BaseModel
from datetime import datetime


class ApplicationCreate(BaseModel):
    name: str
    description: str | None = None
    redirect_uri: str | None = None


class ApplicationUpdate(BaseModel):
    description: str | None = None
    redirect_uri: str | None = None
    is_active: bool | None = None


class ApplicationOut(BaseModel):
    id: int
    name: str
    description: str | None
    api_key: str | None
    redirect_uri: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationOutPublic(BaseModel):
    """Safe schema for external consumers — no api_key exposed."""
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
