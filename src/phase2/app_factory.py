import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.phase2.api.routes import router
from src.phase2.middleware.dynamic_cors import DynamicCORSMiddleware
from src.phase2.middleware.request_id import RequestIDMiddleware

logger = logging.getLogger(__name__)

APP_TITLE = "Restaurant Recommendation API"
APP_DESCRIPTION = "AI-powered restaurant recommendation service inspired by Zomato"
APP_VERSION = "0.2.0"


def configure_app(application: FastAPI, *, api_prefix: str = "/api") -> FastAPI:
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(DynamicCORSMiddleware)
    application.include_router(router, prefix=api_prefix)

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        content: dict = {"detail": exc.detail}
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=exc.status_code, content=content)

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled error [request_id=%s]", request_id)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "request_id": request_id,
            },
        )

    return application


def create_app() -> FastAPI:
    application = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
    )
    return configure_app(application)
