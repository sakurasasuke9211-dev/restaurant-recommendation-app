"""Load deployment secrets into os.environ before application config is imported."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_SECRET_ENV_KEYS = (
    "GROQ_API_KEY",
    "DATABASE_URL",
    "CORS_ORIGINS",
    "LLM_ENABLED",
    "LLM_MODEL",
    "LLM_PROVIDER",
    "LLM_TIMEOUT_SECONDS",
    "LLM_MAX_TOKENS",
    "LLM_TEMPERATURE",
    "LLM_MAX_RETRIES",
    "MAX_RECOMMENDATIONS",
    "MIN_LLM_RECOMMENDATIONS",
)


def _set_env(key: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        os.environ[key] = "true" if value else "false"
    else:
        os.environ[key] = str(value)


def _flatten_toml_secrets(data: dict[str, Any], prefix: str = "") -> None:
    for key, value in data.items():
        env_key = key.upper() if not prefix else f"{prefix}_{key}".upper()
        if isinstance(value, dict):
            _flatten_toml_secrets(value, env_key)
        else:
            _set_env(env_key, value)


def _load_local_secrets_toml() -> None:
    candidates = (
        PROJECT_ROOT / ".streamlit" / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    )
    for secrets_path in candidates:
        if not secrets_path.is_file():
            continue
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore[no-redef]

        with secrets_path.open("rb") as secrets_file:
            _flatten_toml_secrets(tomllib.load(secrets_file))
        return


def _load_process_env() -> None:
    for key in _SECRET_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            os.environ[key] = value


def _load_streamlit_runtime_secrets() -> None:
    try:
        import streamlit as st
    except ImportError:
        return

    try:
        for key in _SECRET_ENV_KEYS:
            if key in st.secrets:
                _set_env(key, st.secrets[key])
    except Exception:
        return


def bootstrap_environment() -> None:
    """Apply Streamlit Cloud / local secrets before importing src.config."""
    _load_process_env()
    _load_local_secrets_toml()
    _load_streamlit_runtime_secrets()
