"""
routes/users.py - User management endpoints (protected)

GET  /users/       → list all users (admin)
GET  /users/me     → current user profile
GET  /users/{id}   → get user by id
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import UserOut
from app.services.user_service import get_user_by_id, get_all_users

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["sub"])
    return get_user_by_id(db, user_id)


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return get_all_users(db)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return get_user_by_id(db, user_id)
