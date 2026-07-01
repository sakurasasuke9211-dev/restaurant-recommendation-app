from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from src.config import get_cors_origins


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """Apply CORS using the latest CORS_ORIGINS env/secrets on each request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        origin = request.headers.get("origin")
        allowed_origins = get_cors_origins()

        if request.method == "OPTIONS" and origin:
            if origin in allowed_origins:
                return PlainTextResponse(
                    status_code=204,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Methods": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Expose-Headers": "X-Request-ID",
                    },
                )
            return PlainTextResponse(status_code=400)

        response = await call_next(request)

        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"

        return response
