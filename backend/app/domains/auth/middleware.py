from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

class SessionTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware skeleton for tracking session active status and resolving IP/User-Agent parameters.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # In a fully-implemented phase, this middleware would update AuthenticationSession's
        # last_activity_at timestamp and verify if the session remains active.
        response = await call_next(request)
        return response
