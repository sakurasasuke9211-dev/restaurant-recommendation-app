"""Production entry point for Streamlit Community Cloud.

Run locally:
    streamlit run streamlit_app.py

This serves the FastAPI REST API at /api/v1/* and a Streamlit status dashboard at /.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from streamlit.web.server.starlette import App as StreamlitApp

from src.phase2.app_factory import APP_DESCRIPTION, APP_TITLE, APP_VERSION, configure_app

_UI_SCRIPT = str(Path(__file__).resolve().parent / "streamlit_ui.py")
st_dashboard = StreamlitApp(_UI_SCRIPT)

_app_configured = False


def _configure_once(application: FastAPI) -> None:
    global _app_configured
    if _app_configured:
        return
    configure_app(application)
    _app_configured = True


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with st_dashboard.lifespan(application):
        from src.deploy.runtime import initialize_runtime

        initialize_runtime()
        _configure_once(application)
        yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.mount("/", st_dashboard)
