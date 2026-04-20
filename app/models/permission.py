"""
models/permission.py - Permission ORM Model (Phase 2: RBAC)

Table: permissions
Columns: id, name, description

Example permissions: read, write, delete, admin:all
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # TODO Phase 2: role_permissions association table se link hoga
