import json
import logging
import os
import time
from typing import Any

from groq import Groq

from src.config import (
    LLM_ENABLED,
    LLM_MAX_RETRIES,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMResponseError(LLMError):
    pass


def _groq_api_key() -> str | None:
    return os.getenv("GROQ_API_KEY")


def is_llm_available() -> bool:
    return LLM_ENABLED and bool(_groq_api_key())


def complete(messages: list[dict[str, str]]) -> str:
    if not is_llm_available():
        raise LLMError("Groq LLM is not available. Set GROQ_API_KEY in .env and LLM_ENABLED=true.")

    client = Groq(api_key=_groq_api_key(), timeout=LLM_TIMEOUT_SECONDS)
    last_error: Exception | None = None

    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMResponseError("Groq returned an empty response")
            return content
        except Exception as exc:
            last_error = exc
            if attempt < LLM_MAX_RETRIES:
                delay = 2**attempt
                logger.warning("Groq request failed (attempt %d), retrying in %ss: %s", attempt + 1, delay, exc)
                time.sleep(delay)
            else:
                logger.error("Groq request failed after %d attempts: %s", LLM_MAX_RETRIES + 1, exc)

    raise LLMError(f"Groq API call failed: {last_error}") from last_error


def parse_llm_response(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"Invalid JSON from Groq: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMResponseError("Groq response must be a JSON object")
    if "summary" not in data or "recommendations" not in data:
        raise LLMResponseError("Groq response missing 'summary' or 'recommendations'")
    if not isinstance(data["recommendations"], list):
        raise LLMResponseError("'recommendations' must be a list")
    return data


def validate_llm_recommendations(
    data: dict[str, Any],
    candidate_ids: set[int],
    max_results: int,
) -> dict[str, Any]:
    valid_items = []
    seen_ranks: set[int] = set()
    seen_ids: set[int] = set()

    for item in data["recommendations"]:
        if not isinstance(item, dict):
            continue
        restaurant_id = item.get("restaurant_id")
        rank = item.get("rank")
        explanation = item.get("explanation")
        if restaurant_id not in candidate_ids or restaurant_id in seen_ids:
            continue
        if not isinstance(rank, int) or rank in seen_ranks:
            continue
        if not explanation or not str(explanation).strip():
            continue
        seen_ranks.add(rank)
        seen_ids.add(restaurant_id)
        valid_items.append(item)
        if len(valid_items) >= max_results:
            break

    valid_items.sort(key=lambda x: x["rank"])
    return {
        "summary": str(data.get("summary", "")).strip(),
        "recommendations": valid_items,
    }
