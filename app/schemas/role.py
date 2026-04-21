from pydantic import BaseModel
from datetime import datetime
from app.schemas.permission import PermissionOut


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    app_id: int | None = None


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    app_id: int | None = None
    created_at: datetime
    permissions: list[PermissionOut] = []

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    role_id: int
    app_id: int | None = None


class AssignPermissionRequest(BaseModel):
    permission_id: int

