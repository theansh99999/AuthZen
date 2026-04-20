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
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.core.config import settings

# ── Import ALL models so they register with Base.metadata ─────
import app.models  # noqa: F401


def create_database_if_not_exists():
    url = settings.DATABASE_URL
    without_scheme = url.replace("postgresql://", "")
    userpass, hostportdb = without_scheme.split("@")
    user, password = userpass.split(":", 1)
    hostport, dbname = hostportdb.rsplit("/", 1)
    host, port = (hostport.split(":") + ["5432"])[:2]
    port = int(port)

    try:
        conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{dbname}"')
            print(f"[IAM] Database '{dbname}' created.")
        else:
            print(f"[IAM] Database '{dbname}' already exists.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[IAM] Warning: Could not auto-create database: {e}")


def seed_defaults():
    """Seed default roles (admin, user) and permissions (read, write, delete) on first run."""
    from app.models.role import Role
    from app.models.permission import Permission

    db = SessionLocal()
    try:
        # ── Permissions ──────────────────────────────────────
        default_perms = [
            ("read",   "Can read resources"),
            ("write",  "Can create and update resources"),
            ("delete", "Can delete resources"),
        ]
        perm_objs = {}
        for name, desc in default_perms:
            p = db.query(Permission).filter_by(name=name).first()
            if not p:
                p = Permission(name=name, description=desc)
                db.add(p)
                db.flush()
                print(f"[IAM] Permission '{name}' created.")
            perm_objs[name] = p

        # ── Roles ─────────────────────────────────────────────
        admin_role = db.query(Role).filter_by(name="admin").first()
        if not admin_role:
            admin_role = Role(name="admin", description="Full access")
            db.add(admin_role)
            db.flush()
            print("[IAM] Role 'admin' created.")
        # admin → all permissions
        admin_role.permissions = list(perm_objs.values())

        user_role = db.query(Role).filter_by(name="user").first()
        if not user_role:
            user_role = Role(name="user", description="Read-only access")
            db.add(user_role)
            db.flush()
            print("[IAM] Role 'user' created.")
        # user → read only
        if perm_objs["read"] not in user_role.permissions:
            user_role.permissions = [perm_objs["read"]]

        db.commit()
        print("[IAM] Default roles & permissions seeded.")
    except Exception as e:
        db.rollback()
        print(f"[IAM] Seed error: {e}")
    finally:
        db.close()


# ── Step 1: DB + Tables ───────────────────────────────────────
create_database_if_not_exists()
Base.metadata.create_all(bind=engine)
print("[IAM] All tables created/verified.")

# ── Step 2: Seed defaults ─────────────────────────────────────
seed_defaults()

app = FastAPI(
    title="IAM Service",
    description="Identity and Access Management — JWT + bcrypt + RBAC",
    version="2.0.0",
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
    return {"status": "ok", "service": "IAM", "version": "2.0.0 (RBAC)"}
