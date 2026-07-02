"""Streamlit Community Cloud entry point (admin dashboard only).

Run locally:
    streamlit run streamlit_app.py

The REST API runs separately:
    uvicorn src.phase2.main:app --reload --port 8000

Production API is hosted on Render; Vercel proxies /api/* there.
"""

from __future__ import annotations

import importlib

from src.deploy.env import bootstrap_environment

bootstrap_environment()

from src.deploy.runtime import initialize_runtime

initialize_runtime()

import streamlit_ui

importlib.reload(streamlit_ui)
