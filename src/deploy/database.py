"""Ensure the SQLite database exists before serving requests on Streamlit Cloud."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from src.config import DEFAULT_DB_PATH

logger = logging.getLogger(__name__)


def _running_on_streamlit_cloud() -> bool:
    """Best-effort detection of Streamlit Community Cloud runtime."""
    return any(
        os.environ.get(key)
        for key in (
            "STREAMLIT_SHARING_MODE",
            "STREAMLIT_SERVER_PORT",
            "STREAMLIT_SERVER_HEADLESS",
        )
    )


def database_exists() -> bool:
    return DEFAULT_DB_PATH.is_file() and DEFAULT_DB_PATH.stat().st_size > 0


def ensure_database() -> None:
    """Verify the restaurant database exists before serving traffic."""
    if database_exists():
        logger.info("Database found at %s", DEFAULT_DB_PATH)
        return

    message = (
        f"Database missing at {DEFAULT_DB_PATH}. "
        "Commit data/processed/restaurants.db or set DATABASE_URL to a valid SQLite file."
    )

    if _running_on_streamlit_cloud():
        # Avoid Hugging Face ingestion on Cloud: it exceeds memory/startup time limits
        # and prevents the Streamlit health check from passing.
        raise FileNotFoundError(message)

    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.warning("%s Running one-time local ingestion...", message)

    from src.phase1.ingest import run_ingestion

    run_ingestion(reset=True)
    logger.info("Ingestion complete — %s", DEFAULT_DB_PATH)
