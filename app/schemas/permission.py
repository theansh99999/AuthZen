from pydantic import BaseModel
from datetime import datetime


class PermissionOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionCreate(BaseModel):
    name: str
    description: str | None = None
