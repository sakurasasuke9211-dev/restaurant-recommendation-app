from contextlib import asynccontextmanager

from src.deploy.env import bootstrap_environment

bootstrap_environment()

from fastapi import FastAPI

from src.deploy.runtime import initialize_runtime
from src.phase2.app_factory import APP_DESCRIPTION, APP_TITLE, APP_VERSION, configure_app


@asynccontextmanager
async def lifespan(_application: FastAPI):
    initialize_runtime()
    yield


application = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)
app = configure_app(application)


@app.get("/")
def api_root() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "restaurant-recommendation-api",
        "health": "/api/v1/health",
        "docs": "/docs",
    }
