"""
models/auth_code.py - Short-lived authorization codes for OAuth2 flow

Flow:
  /authorize → user login → generate auth_code → redirect to redirect_uri?code=XXX
  /token → exchange code for JWT access_token
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from app.db.base import Base


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(128), unique=True, nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    app_id      = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    redirect_uri= Column(String(500), nullable=False)
    state       = Column(String(256), nullable=True)   # CSRF state param
    used        = Column(Boolean, default=False)
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
