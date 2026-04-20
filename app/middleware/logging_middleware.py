"""
middleware/logging_middleware.py - Request/Response logging middleware

Logs: method, path, status_code, process_time for every request
Phase 7 me audit_log table se integrate hoga.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("iam.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)"
        )
        return response
