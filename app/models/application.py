"""
models/application.py - Application ORM Model (Phase 4: Multi-App Support)

Table: applications
Columns: id, name, description, is_active, created_at

Ek hi IAM system multiple apps ko serve karega.
Har app ke apne roles aur permissions honge.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(300), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # TODO Phase 4: user_roles me app_id foreign key add hoga
