"""
schemas/iam.py - Request & Response schemas for reusable IAM service external endpoints
"""

from pydantic import BaseModel, ConfigDict
from .user import UserOut


class TokenValidationRequest(BaseModel):
    # Optional because it can come from Authorization Header or Request Body
    token: str | None = None
    
    
class TokenValidationResponse(BaseModel):
    is_valid: bool
    user: UserOut | None = None
    error: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class PermissionCheckRequest(BaseModel):
    # Optional token, can be from Authorization header
    token: str | None = None
    permission: str
    app_id: int | None = None


class PermissionCheckResponse(BaseModel):
    has_permission: bool
    error: str | None = None
