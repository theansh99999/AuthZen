"""
dependencies.py - Reusable FastAPI dependencies

get_current_user:
  → Bearer token extract karo
  → Decode karo
  → DB se user fetch karo
  → Inject karo as current user
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    TODO (Phase 1): Implement full logic —
      1. decode_access_token(token)
      2. Extract user_id from payload
      3. Query DB for user
      4. Raise 401 if invalid/expired
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload  # placeholder — replace with actual User object
