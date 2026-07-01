"""Phase 3 — Integration Layer (filter pipeline, prompt builder, Groq LLM)."""

from src.phase3.filter import FilterResult, FilterService, score_keyword_match
from src.phase3.llm import (
    LLMError,
    LLMResponseError,
    complete,
    is_llm_available,
    parse_llm_response,
    validate_llm_recommendations,
)
from src.phase3.prompt import build_prompt, estimate_token_count, restaurant_to_llm_dict

__all__ = [
    "FilterResult",
    "FilterService",
    "score_keyword_match",
    "LLMError",
    "LLMResponseError",
    "complete",
    "is_llm_available",
    "parse_llm_response",
    "validate_llm_recommendations",
    "build_prompt",
    "estimate_token_count",
    "restaurant_to_llm_dict",
]
