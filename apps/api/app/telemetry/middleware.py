"""
Middleware לטלמטריית בקשות — רישום מטריקות בקשה/תגובה.
MVP: לוגינג מובנה. לאחר MVP: spans של OpenTelemetry.
"""
import time
import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("cognet.api.telemetry")


class RequestTelemetryMiddleware(BaseHTTPMiddleware):
    """רישום משך בקשה, קוד סטטוס ונתיב לכל קריאת API."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        # הוספת request_id למצב הבקשה לשימוש downstream
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )
            raise

        duration_ms = int((time.monotonic() - start) * 1000)

        # רישום בקשות שאינן health (למניעת לוגים רועשים של בדיקות בריאות)
        if request.url.path not in ("/health", "/ready"):
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

        response.headers["X-Request-ID"] = request_id
        return response
