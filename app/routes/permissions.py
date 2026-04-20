"""
routes/permissions.py - Permission management endpoints (Phase 2: RBAC)

POST /permissions/               → create permission
GET  /permissions/               → list permissions
POST /permissions/{id}/assign    → assign permission to role
"""

from fastapi import APIRouter

router = APIRouter()

# TODO Phase 2: Implement RBAC permission routes
