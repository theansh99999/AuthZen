"""
services/application_service.py - Multi-app management and role mappings
"""

from sqlalchemy.orm import Session
from sqlalchemy import insert
from fastapi import HTTPException
from app.models.application import Application
from app.models.user import User
from app.models.role import Role
from app.schemas.application import ApplicationCreate
from app.models.associations import user_roles


def create_application(db: Session, data: ApplicationCreate) -> Application:
    if db.query(Application).filter(Application.name == data.name).first():
        raise HTTPException(status_code=400, detail="Application name already exists.")
    app = Application(name=data.name, description=data.description)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def get_all_applications(db: Session) -> list[Application]:
    return db.query(Application).all()


def assign_role_to_user_for_app(db: Session, user_id: int, role_id: int, app_id: int) -> dict:
    """
    Directly assigns a role to a user specifically for an application via the association table.
    Validates that the role belongs to the app requested (or is a global role).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")
        
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
        
    if role.app_id is not None and role.app_id != app_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Role '{role.name}' does not belong to application '{application.name}'."
        )
        
    # Check if this mapping already exists
    stmt = db.query(user_roles).filter_by(user_id=user_id, role_id=role_id, app_id=app_id)
    if stmt.first():
        raise HTTPException(status_code=400, detail="User already has this role for this application.")
        
    # Insert raw statement since we cannot just do user.roles.append() while targeting app_id cleanly
    db.execute(
        insert(user_roles).values(user_id=user_id, role_id=role_id, app_id=app_id)
    )
    db.commit()
    
    return {"message": f"Assigned role '{role.name}' to user '{user.username}' for app '{application.name}'."}
