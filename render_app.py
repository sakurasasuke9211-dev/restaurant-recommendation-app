"""Render.com entry point — use: uvicorn render_app:app --host 0.0.0.0 --port $PORT"""

from src.phase2.main import app

__all__ = ["app"]
