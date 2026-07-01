"""Streamlit admin dashboard shown at the app root on Streamlit Community Cloud."""

from __future__ import annotations

from src.deploy.env import bootstrap_environment

bootstrap_environment()

import streamlit as st

from src.config import CORS_ORIGINS, DATABASE_URL, DEFAULT_DB_PATH, LLM_ENABLED, LLM_MODEL, PROJECT_ROOT
from src.phase1.database import get_session
from src.phase1.loader import RestaurantRepository
from src.phase3.llm import is_llm_available

st.set_page_config(
    page_title="Restaurant Recommendation API",
    page_icon="🍽️",
    layout="wide",
)

st.title("Restaurant Recommendation API")
st.caption("FastAPI backend on Streamlit Community Cloud")

col1, col2, col3 = st.columns(3)

try:
    with get_session() as session:
        restaurant_count = RestaurantRepository(session).count_all()
    db_status = "connected"
except Exception as exc:
    restaurant_count = 0
    db_status = f"error: {exc}"

if not DEFAULT_DB_PATH.is_file():
    st.error(
        f"Database file not found at `{DEFAULT_DB_PATH}`. "
        "Push `data/processed/restaurants.db` to GitHub or wait for first-run ingestion to finish."
    )

col1.metric("Restaurants", f"{restaurant_count:,}")
col2.metric("Database", db_status)
col3.metric("LLM", "available" if is_llm_available() else "offline")

if not is_llm_available():
    st.warning("Set `GROQ_API_KEY` in Streamlit Cloud → Settings → Secrets, then reboot the app.")

with st.expander("Configuration", expanded=False):
    st.write(f"**Database URL:** `{DATABASE_URL}`")
    st.write(f"**LLM enabled:** `{LLM_ENABLED}`")
    st.write(f"**LLM model:** `{LLM_MODEL}`")
    st.write(f"**CORS origins:** `{', '.join(CORS_ORIGINS)}`")
    st.write(f"**Project root:** `{PROJECT_ROOT}`")

st.subheader("REST API")
st.markdown(
    """
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/meta/cities` | List cities |
| `GET` | `/api/v1/meta/areas` | List areas |
| `GET` | `/api/v1/meta/cuisines` | List cuisines |
| `POST` | `/api/v1/recommendations` | Get recommendations |
"""
)

st.info(
    "Point the Vercel frontend `VITE_API_URL` at this app's public URL "
    "(no trailing slash). Example: `https://your-app.streamlit.app`"
)
