from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.container import get_rate_limiter

F = TypeVar("F", bound=Callable[..., Response])


def RateLimit(
    reqs: Optional[int] = None,
    window: Optional[int] = None,
    key_func: Optional[Callable[[Request], str]] = None,
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            key = key_func(request) if key_func else (request.client.host if request.client else "unknown")

            limiter = get_rate_limiter()
            result = limiter.limit(key, reqs, window)

            if not result.allowed:
                if result.reason == "rate_limit_exceeded":
                    raise HTTPException(429, detail="Too many requests")
                else:
                    raise HTTPException(503, detail="Service temporarily unavailable")

            response = func(request, *args, **kwargs)
            if limiter.enabled is False:
                return response

            if response.status_code >= 400:
                limiter.record_error(key)
            else:
                limiter.record_success(key)
            return response

        return cast(F, wrapper)

    return decorator
