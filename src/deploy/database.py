"""Ensure the SQLite database exists before serving requests on Streamlit Cloud."""

from __future__ import annotations

import logging
from pathlib import Path

from src.config import DEFAULT_DB_PATH

logger = logging.getLogger(__name__)


def database_exists() -> bool:
    return DEFAULT_DB_PATH.is_file() and DEFAULT_DB_PATH.stat().st_size > 0


def ensure_database() -> None:
    """Create the restaurant database from Hugging Face if it is missing."""
    if database_exists():
        logger.info("Database found at %s", DEFAULT_DB_PATH)
        return

    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.warning(
        "Database missing at %s — running one-time ingestion (may take a few minutes)...",
        DEFAULT_DB_PATH,
    )

    from src.phase1.ingest import run_ingestion

    run_ingestion(reset=True)
    logger.info("Ingestion complete — %s", DEFAULT_DB_PATH)
