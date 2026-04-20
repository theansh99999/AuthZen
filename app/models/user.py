"""
models/user.py - User ORM Model

Table: users
Columns: id, username, email, password_hash, is_active, created_at

Phase 1: Base auth
Phase 2: RBAC ke liye user_roles relationship add hoga
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # TODO Phase 2: Add relationships
    # roles = relationship("Role", secondary="user_roles", back_populates="users")
