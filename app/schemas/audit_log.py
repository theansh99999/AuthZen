from pydantic import BaseModel
from datetime import datetime
from typing import Any

class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    ip_address: str | None
    meta: dict[str, Any] | None
    timestamp: datetime

    class Config:
        from_attributes = True
