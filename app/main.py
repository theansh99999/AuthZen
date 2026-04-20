"""
main.py - FastAPI application entry point
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.logging_middleware import LoggingMiddleware
from app.routes import auth, users, roles, permissions, applications, audit_logs
from app.routes import pages
from app.db.session import engine
from app.db.base import Base
from app.core.config import settings


def create_database_if_not_exists():
    """
    PostgreSQL me target database create karo agar exist nahi karta.
    Default 'postgres' DB se connect karke check karta hai.
    """
    # DATABASE_URL se parts extract karo
    # Format: postgresql://user:password@host:port/dbname
    url = settings.DATABASE_URL
    # Parse: postgresql://user:pass@host:port/dbname
    without_scheme = url.replace("postgresql://", "")
    userpass, hostportdb = without_scheme.split("@")
    user, password = userpass.split(":", 1)
    hostport, dbname = hostportdb.rsplit("/", 1)
    if ":" in hostport:
        host, port = hostport.split(":")
        port = int(port)
    else:
        host = hostport
        port = 5432

    try:
        # Default 'postgres' database se connect karo
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if DB exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f'CREATE DATABASE "{dbname}"')
            print(f"[IAM] Database '{dbname}' created successfully.")
        else:
            print(f"[IAM] Database '{dbname}' already exists.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[IAM] Warning: Could not auto-create database: {e}")


# ── Step 1: Create DB if not exists ──────────────────────────
create_database_if_not_exists()

# ── Step 2: Create all tables ─────────────────────────────────
Base.metadata.create_all(bind=engine)
print("[IAM] All tables created/verified.")

app = FastAPI(
    title="IAM Service",
    description="Identity and Access Management — JWT + bcrypt + RBAC",
    version="1.0.0",
)

# ── Middleware ────────────────────────────────────────────────
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Web (Jinja2) Routes ───────────────────────────────────────
app.include_router(pages.router, tags=["Web UI"])

# ── API Routes ────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/auth",        tags=["Auth API"])
app.include_router(users.router,        prefix="/users",       tags=["Users API"])
app.include_router(roles.router,        prefix="/roles",       tags=["Roles API"])
app.include_router(permissions.router,  prefix="/permissions", tags=["Permissions API"])
app.include_router(applications.router, prefix="/apps",        tags=["Applications API"])
app.include_router(audit_logs.router,   prefix="/logs",        tags=["Audit Logs API"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "IAM"}
