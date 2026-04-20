"""
schemas/user.py - Pydantic schemas for User

UserCreate  → signup request body
UserLogin   → login request body
UserOut     → response (password hash exclude)
Token       → JWT token response
TokenData   → decoded JWT payload
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
