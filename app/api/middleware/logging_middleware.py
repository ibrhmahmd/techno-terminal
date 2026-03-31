"""
app/api/middleware/logging_middleware.py
────────────────────────────────────────
Request/response access logger.

Logs every API call with:
  - A short random request ID (injected into the response as X-Request-ID)
  - HTTP method and path
  - Response status code
  - Wall-clock latency in milliseconds

The request ID makes it trivial to correlate a client error report
with the exact server-side trace.

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


async def logging_middleware(request: Request, call_next) -> Response:
    request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()

    response: Response = await call_next(request)

    latency_ms = round((time.perf_counter() - start) * 1000)

    logger.info(
        "[%s] %s %s → %d  (%dms)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        latency_ms,
    )

    response.headers["X-Request-ID"] = request_id
    return response
