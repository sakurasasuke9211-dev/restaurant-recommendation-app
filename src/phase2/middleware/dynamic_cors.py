from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from src.config import get_cors_origins


def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/")


def _is_origin_allowed(origin: str, allowed_origins: list[str]) -> bool:
    normalized = _normalize_origin(origin)
    return any(_normalize_origin(allowed) == normalized for allowed in allowed_origins)


def _cors_headers(origin: str) -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID",
        "Access-Control-Expose-Headers": "X-Request-ID",
        "Vary": "Origin",
    }


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """Apply CORS using the latest CORS_ORIGINS env/secrets on each request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        origin = request.headers.get("origin")
        allowed = origin is not None and _is_origin_allowed(origin, get_cors_origins())

        if request.method == "OPTIONS" and origin:
            if allowed:
                return PlainTextResponse(status_code=204, headers=_cors_headers(origin))
            return PlainTextResponse(status_code=403)

        response = await call_next(request)

        if allowed and origin:
            response.headers.update(_cors_headers(origin))

        return response
