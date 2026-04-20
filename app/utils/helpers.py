"""
utils/helpers.py - Reusable utility functions

Examples:
  - paginate(query, skip, limit) → paginated results
  - get_client_ip(request) → IP string
"""

from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers or client info."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def paginate(query, skip: int = 0, limit: int = 50):
    """Apply pagination to a SQLAlchemy query."""
    return query.offset(skip).limit(limit).all()
