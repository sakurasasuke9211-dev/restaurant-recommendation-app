import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_DB_PATH = DATA_DIR / "restaurants.db"


def resolve_database_url(raw: str | None = None) -> str:
    """Normalize SQLite URLs so relative paths resolve from the project root."""
    url = (raw or os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return f"sqlite:///{DEFAULT_DB_PATH.resolve().as_posix()}"

    if not url.startswith("sqlite:"):
        return url

    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url

    path_part = url[len(prefix) :]
    if path_part in ("", ":memory:"):
        return url

    db_path = Path(path_part)
    if not db_path.is_absolute():
        db_path = (PROJECT_ROOT / db_path).resolve()
    return f"sqlite:///{db_path.as_posix()}"


DATABASE_URL = resolve_database_url()

DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"
DATASET_SPLIT = "train"

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]


def get_cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

MAX_RECOMMENDATIONS = int(os.getenv("MAX_RECOMMENDATIONS", "5"))
LLM_CANDIDATE_COUNT = 20
MIN_LLM_RECOMMENDATIONS = int(os.getenv("MIN_LLM_RECOMMENDATIONS", "3"))
BUDGET_RELAXATION_INCREMENT = 200
BUDGET_RELAXATION_STEPS = 2

# Groq LLM (Phase 3)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() in {"1", "true", "yes"}
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2500"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
