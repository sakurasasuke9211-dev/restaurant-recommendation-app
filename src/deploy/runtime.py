"""Runtime initialization for Streamlit Cloud after secrets and environment are ready."""

from __future__ import annotations

import importlib
import logging

from src.deploy.database import ensure_database
from src.deploy.env import bootstrap_environment

logger = logging.getLogger(__name__)

_initialized = False


def initialize_runtime() -> None:
    """Load secrets, refresh config/database bindings, and ensure SQLite exists."""
    global _initialized
    if _initialized:
        return

    bootstrap_environment()

    import src.config as config
    import src.phase1.database as database

    importlib.reload(config)
    importlib.reload(database)

    ensure_database()
    _initialized = True
    logger.info("Streamlit runtime initialized (db=%s)", config.DEFAULT_DB_PATH)
