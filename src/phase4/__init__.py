"""Phase 4 — Recommendation Engine (validation, enrichment, fallback ranker)."""

from src.phase4.engine import RecommendationEngine, validate_and_normalize_llm_output
from src.phase4.ranker import (
    build_fallback_explanation,
    build_fallback_recommendations,
    rank_candidates,
    score_restaurant,
)

__all__ = [
    "RecommendationEngine",
    "validate_and_normalize_llm_output",
    "build_fallback_explanation",
    "build_fallback_recommendations",
    "rank_candidates",
    "score_restaurant",
]
