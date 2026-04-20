"""
main.py - FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.routes import auth, users, roles, permissions, applications, audit_logs

app = FastAPI(
    title="IAM Service",
    description="Identity and Access Management System — JWT + RBAC + Multi-App",
    version="1.0.0",
)

# Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(roles.router, prefix="/roles", tags=["Roles"])
app.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
app.include_router(applications.router, prefix="/apps", tags=["Applications"])
app.include_router(audit_logs.router, prefix="/logs", tags=["Audit Logs"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "IAM"}
