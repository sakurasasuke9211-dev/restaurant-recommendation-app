"""Production entry point for Streamlit Community Cloud.

Run locally:
    streamlit run streamlit_app.py

Streamlit UI is served at /. REST API routes are mounted at /api/v1/* via st.App routes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from src.deploy.env import bootstrap_environment

bootstrap_environment()

from fastapi import FastAPI
from starlette.routing import Mount
from streamlit.web.server.starlette import App as StreamlitApp

from src.phase2.app_factory import APP_DESCRIPTION, APP_TITLE, APP_VERSION, configure_app

_UI_SCRIPT = str(Path(__file__).resolve().parent / "streamlit_ui.py")


@asynccontextmanager
async def _streamlit_startup(_st_app):
    """Runs after Streamlit loads secrets and prepares the runtime environment."""
    from src.deploy.runtime import initialize_runtime

    initialize_runtime()
    yield


def _create_mounted_api() -> FastAPI:
    """API sub-app mounted at /api → public paths like /api/v1/health."""
    api_app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
    )
    return configure_app(api_app, api_prefix="")


app = StreamlitApp(
    _UI_SCRIPT,
    lifespan=_streamlit_startup,
    routes=[Mount("/api", app=_create_mounted_api())],
)
