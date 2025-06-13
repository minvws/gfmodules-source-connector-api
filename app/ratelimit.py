from functools import wraps
from typing import Optional

from fastapi import HTTPException
from starlette.requests import Request

from app.container import get_rate_limiter


def RateLimit(
    reqs: Optional[int] = None,
    window: Optional[int] = None,
    key_func=None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            key = key_func(request) if key_func else request.client.host

            # Check if the rate limiter (and/or circuit breaker) is triggered
            limiter = get_rate_limiter()
            result = limiter.limit(key, reqs, window)
            if result.allowed == False:
                if result.reason == "rate_limit_exceeded":
                    raise HTTPException(429, detail=f"Too many requests")
                else:
                    raise HTTPException(503, detail="Service temporarily unavailable")

            response = func(request, *args, **kwargs)

            # Record success or error based on response status. This will be used in the circuit breaking logic.
            if response.status_code >= 400:
                limiter.record_error(key)
            else:
                limiter.record_success(key)
            return response
        return wrapper
    return decorator
