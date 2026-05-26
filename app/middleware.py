from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


CSRF_COOKIE_NAME = "csrf_token"
CSRF_EXCLUDE_PATHS = {"/api/v1/metrics"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        if request.url.path in CSRF_EXCLUDE_PATHS:
            return await call_next(request)

        token_header = request.headers.get("X-CSRF-Token", "")
        token_cookie = request.cookies.get(CSRF_COOKIE_NAME, "")

        if not token_header or not token_cookie or token_header != token_cookie:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch"}
            )

        return await call_next(request)
