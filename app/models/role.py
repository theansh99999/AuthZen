from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.associations import user_roles, role_permissions


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint('app_id', 'name', name='roles_app_id_name_key'),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    app_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application")
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
