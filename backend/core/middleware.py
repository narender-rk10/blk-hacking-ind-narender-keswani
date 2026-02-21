"""Request timing and memory tracking middleware."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from core.performance_monitor import PerformanceMonitor


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that measures request duration and records it
    in the PerformanceMonitor singleton.
    Adds X-Response-Time header to every response.
    """

    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        PerformanceMonitor().record_request(duration)
        response.headers["X-Response-Time"] = f"{duration:.4f}s"
        return response
