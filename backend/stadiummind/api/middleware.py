"""HTTP middleware: security headers and rate limiting.

Both are dependency-free (no Redis required for the limiter's default mode) so
the gateway is hardened out of the box. In a multi-instance deployment the
limiter should be backed by the shared Redis store; the in-process limiter here
is correct for a single instance and for tests.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach standard hardening headers to every response.

    The API serves JSON only, so a very strict CSP (`default-src 'none'`) is
    appropriate and blocks any accidental HTML/script execution. HSTS is only
    emitted in production (it is meaningless / harmful over plain HTTP in dev).
    """

    def __init__(self, app, *, production: bool) -> None:
        super().__init__(app)
        self._production = production

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        # Do not let intermediaries cache authenticated API data.
        response.headers.setdefault("Cache-Control", "no-store")
        if self._production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client-IP rate limiter.

    Limits requests to ``limit_per_minute`` per client IP. The health check is
    always exempt so liveness probes are never throttled. Returns HTTP 429 with
    a ``Retry-After`` header when the budget is exceeded.
    """

    _EXEMPT_PATHS = frozenset({"/api/health"})

    def __init__(self, app, *, limit_per_minute: int) -> None:
        super().__init__(app)
        self._limit = limit_per_minute
        self._lock = threading.Lock()
        # client_ip -> (window_start_epoch, count)
        self._buckets: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))

    async def dispatch(self, request: Request, call_next) -> Response:
        if self._limit <= 0 or request.url.path in self._EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        with self._lock:
            window_start, count = self._buckets[client_ip]
            if now - window_start >= 60.0:
                # New window.
                self._buckets[client_ip] = (now, 1)
            elif count >= self._limit:
                retry_after = max(1, int(60.0 - (now - window_start)))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)},
                )
            else:
                self._buckets[client_ip] = (window_start, count + 1)
        return await call_next(request)
