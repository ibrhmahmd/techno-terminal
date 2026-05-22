"""
app/api/middleware/logging_middleware.py
────────────────────────────────────────
Request/response access logger.

Logs every API call with:
  - A short random request ID (injected into the response as X-Request-ID)
  - HTTP method and path
  - Response status code
  - Wall-clock latency in milliseconds

Slow requests (≥slow_request_ms) are logged at WARNING level.
Health check endpoints are logged at DEBUG level.

Mounted in main.py via:
    from starlette.middleware.base import BaseHTTPMiddleware
    from app.api.middleware.logging_middleware import logging_middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
"""
import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import Response

logger = logging.getLogger("api.access")

# Paths to suppress from normal INFO logging (logged at DEBUG)
_HEALTH_PATHS = {"/health", "/kaithhealthcheck"}


async def logging_middleware(request: Request, call_next) -> Response:
    request_id = uuid.uuid4().hex[:8]
    from app.db.query_logger import set_db_request_id

    set_db_request_id(request_id)
    start = time.perf_counter()

    response: Response = await call_next(request)

    latency_ms = round((time.perf_counter() - start) * 1000)

    is_health = request.url.path in _HEALTH_PATHS
    is_slow = latency_ms >= getattr(request.app.state, "slow_request_ms", 5000)

    level = logging.DEBUG if is_health else (logging.WARNING if is_slow else logging.INFO)

    logger.log(
        level,
        "[%s] %s %s → %d  (%dms)%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        latency_ms,
        "  SLOW" if is_slow else "",
    )

    response.headers["X-Request-ID"] = request_id
    return response
