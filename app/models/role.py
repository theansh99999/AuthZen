"""
models/role.py - Role ORM Model (Phase 2: RBAC)

Table: roles
Columns: id, name, description, created_at

Example roles: admin, user, moderator
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # TODO Phase 2: Add relationships
    # permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    # users = relationship("User", secondary="user_roles", back_populates="roles")
