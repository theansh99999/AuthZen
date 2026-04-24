"""
utils/rate_limit.py - Basic in-memory rate limiting mechanism.

It prevents spam on the external API.
In production, you'd use Redis and a library like slowapi.
"""

from fastapi import Request, HTTPException, status
import time

# Simple in-memory tracker: { "ip_address": [timestamp1, timestamp2, ...] }
RATE_LIMIT_CACHE: dict[str, list[float]] = {}
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60

def rate_limiter(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key")
    
    # Track by API key if present, otherwise IP
    identifier = f"api_key:{api_key}" if api_key else f"ip:{client_ip}"
    
    current_time = time.time()
    
    if identifier not in RATE_LIMIT_CACHE:
        RATE_LIMIT_CACHE[identifier] = []
        
    # Remove old timestamps outside of window
    requests_in_window = [
        ts for ts in RATE_LIMIT_CACHE[identifier] 
        if current_time - ts < RATE_LIMIT_WINDOW_SECONDS
    ]
    
    if len(requests_in_window) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
        
    requests_in_window.append(current_time)
    RATE_LIMIT_CACHE[identifier] = requests_in_window
