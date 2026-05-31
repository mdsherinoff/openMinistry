import time
import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}"
        )

        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"[{request_id}] {response.status_code} "
                f"{request.url.path} {duration:.0f}ms"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] ERROR {request.url.path} "
                f"{duration:.0f}ms — {e}"
            )
            raise