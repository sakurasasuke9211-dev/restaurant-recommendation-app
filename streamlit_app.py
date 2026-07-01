"""Production entry point for Streamlit Community Cloud.

Run locally:
    streamlit run streamlit_app.py

This serves the FastAPI REST API at /api/v1/* and a Streamlit status dashboard at /.
"""

from __future__ import annotations

from pathlib import Path

from src.deploy.env import bootstrap_environment

bootstrap_environment()

from fastapi import FastAPI
from streamlit.web.server.starlette import App as StreamlitApp

from src.phase2.app_factory import APP_DESCRIPTION, APP_TITLE, APP_VERSION, configure_app

_UI_SCRIPT = str(Path(__file__).resolve().parent / "streamlit_ui.py")

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

configure_app(app)

st_dashboard = StreamlitApp(_UI_SCRIPT)
app.mount("/", st_dashboard)
