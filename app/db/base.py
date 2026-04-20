"""
base.py - SQLAlchemy declarative base

Sare ORM models is Base ko inherit karenge.
Alembic bhi isi Base se migrations generate karega.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
