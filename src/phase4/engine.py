import logging
from typing import Any

from src.config import MAX_RECOMMENDATIONS
from src.phase1.constants import RELAXATION_LABELS
from src.phase1.loader import deserialize_json_list
from src.phase1.schema import Restaurant
from src.phase2.api.schemas import (
    RecommendationItem,
    RecommendationMeta,
    RecommendationResponse,
    UserPreferences,
)
from src.phase3.llm import (
    LLMError,
    LLMResponseError,
    complete,
    is_llm_available,
    parse_llm_response,
)
from src.phase3.prompt import build_prompt
from src.phase4.ranker import (
    build_fallback_explanation,
    build_fallback_recommendations,
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Phase 4 engine: Groq ranking, validation, enrichment, and fallback."""

    def run(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        filters_relaxed: bool,
        processing_time_ms: int = 0,
        relaxation_steps: list[str] | None = None,
        budget_blocked: bool = False,
    ) -> RecommendationResponse:
        steps = relaxation_steps or []
        if candidates and is_llm_available():
            try:
                return self._run_groq(
                    preferences,
                    candidates,
                    filters_relaxed,
                    processing_time_ms,
                    steps,
                    budget_blocked,
                )
            except (LLMError, LLMResponseError) as exc:
                logger.warning("Groq engine failed, using fallback ranker: %s", exc)

        return self._run_fallback(
            preferences,
            candidates,
            filters_relaxed,
            processing_time_ms,
            steps,
            budget_blocked,
        )

    def _run_groq(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        filters_relaxed: bool,
        processing_time_ms: int,
        relaxation_steps: list[str],
        budget_blocked: bool,
    ) -> RecommendationResponse:
        messages = build_prompt(preferences, candidates)
        raw = self._complete_with_parse_retry(messages)
        parsed = parse_llm_response(raw)
        candidate_map = {r.id: r for r in candidates}

        validated = validate_and_normalize_llm_output(
            parsed,
            candidate_map=candidate_map,
            preferences=preferences,
            max_results=MAX_RECOMMENDATIONS,
        )

        if not validated:
            raise LLMResponseError("No valid recommendations after validation")

        recommendations = sort_recommendations_by_rating(
            ensure_recommendation_count(
                validated, candidates, preferences, MAX_RECOMMENDATIONS
            )
        )

        summary = str(parsed.get("summary", "")).strip() or _build_summary(
            preferences, len(recommendations), filters_relaxed
        )

        return RecommendationResponse(
            summary=summary,
            recommendations=recommendations,
            meta=RecommendationMeta(
                total_candidates=len(candidates),
                filters_relaxed=filters_relaxed,
                llm_used=True,
                processing_time_ms=processing_time_ms,
                relaxation_steps=_humanize_relaxation_steps(relaxation_steps),
                budget_blocked=budget_blocked,
            ),
        )

    def _run_fallback(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        filters_relaxed: bool,
        processing_time_ms: int,
        relaxation_steps: list[str],
        budget_blocked: bool,
    ) -> RecommendationResponse:
        recommendations = sort_recommendations_by_rating(
            ensure_recommendation_count(
                [], candidates, preferences, MAX_RECOMMENDATIONS
            )
        )
        return RecommendationResponse(
            summary=_build_summary(preferences, len(recommendations), filters_relaxed),
            recommendations=recommendations,
            meta=RecommendationMeta(
                total_candidates=len(candidates),
                filters_relaxed=filters_relaxed,
                llm_used=False,
                processing_time_ms=processing_time_ms,
                relaxation_steps=_humanize_relaxation_steps(relaxation_steps),
                budget_blocked=budget_blocked,
            ),
        )

    def _complete_with_parse_retry(self, messages: list[dict[str, str]]) -> str:
        raw = complete(messages)
        try:
            parse_llm_response(raw)
            return raw
        except LLMResponseError:
            logger.warning("JSON parse failed on first Groq response, retrying once")
            raw = complete(messages)
            parse_llm_response(raw)
            return raw


def _parse_restaurant_id(item: dict[str, Any]) -> int | None:
    raw = item.get("restaurant_id", item.get("id"))
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def validate_and_normalize_llm_output(
    data: dict[str, Any],
    candidate_map: dict[int, Restaurant],
    preferences: UserPreferences,
    max_results: int,
) -> list[RecommendationItem]:
    candidate_ids = set(candidate_map)
    raw_items = data.get("recommendations", [])
    if not isinstance(raw_items, list):
        return []

    collected: list[tuple[int, RecommendationItem]] = []
    seen_ids: set[int] = set()
    seen_ranks: set[int] = set()

    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        restaurant_id = _parse_restaurant_id(item)
        if restaurant_id is None or restaurant_id not in candidate_ids or restaurant_id in seen_ids:
            continue

        restaurant = candidate_map[restaurant_id]
        rank = item.get("rank")
        if not isinstance(rank, int) or rank in seen_ranks:
            rank = index + 1
        while rank in seen_ranks:
            rank += 1
        seen_ranks.add(rank)
        seen_ids.add(restaurant_id)

        explanation = str(item.get("explanation") or "").strip()
        if not explanation:
            explanation = build_fallback_explanation(restaurant, preferences)

        cuisines = deserialize_json_list(restaurant.cuisines)
        collected.append(
            (
                rank,
                RecommendationItem(
                    rank=rank,
                    restaurant_id=restaurant.id,
                    name=restaurant.name,
                    area=restaurant.area,
                    cuisines=cuisines,
                    rating=restaurant.rating,
                    cost_for_two=restaurant.cost_for_two,
                    price_range=restaurant.price_range,
                    explanation=explanation,
                ),
            )
        )
        if len(collected) >= max_results:
            break

    collected.sort(key=lambda pair: pair[0])
    result: list[RecommendationItem] = []
    for new_rank, (_, item) in enumerate(collected[:max_results], start=1):
        item.rank = new_rank
        result.append(item)
    return result


def ensure_recommendation_count(
    items: list[RecommendationItem],
    candidates: list[Restaurant],
    preferences: UserPreferences,
    target_count: int,
) -> list[RecommendationItem]:
    """Fill to target_count (usually 5) using fallback ranker when LLM returns fewer."""
    target = min(target_count, len(candidates))
    if target == 0:
        return []

    if len(items) >= target:
        return items[:target]

    used_ids = {item.restaurant_id for item in items}
    supplements = build_fallback_recommendations(
        candidates,
        preferences,
        exclude_ids=used_ids,
        limit=target - len(items),
    )

    combined = list(items)
    next_rank = len(combined) + 1
    for item in supplements:
        item.rank = next_rank
        combined.append(item)
        next_rank += 1

    return combined[:target]


def sort_recommendations_by_rating(
    items: list[RecommendationItem],
) -> list[RecommendationItem]:
    """Order results by rating (highest first) and re-number rank badges."""
    sorted_items = sorted(
        items,
        key=lambda item: (
            item.rating if item.rating is not None else -1.0,
            item.name.lower(),
        ),
        reverse=True,
    )
    for rank, item in enumerate(sorted_items, start=1):
        item.rank = rank
    return sorted_items


def _humanize_relaxation_steps(steps: list[str]) -> list[str]:
    return [RELAXATION_LABELS.get(step, step.replace("_", " ")) for step in steps]


def _build_summary(
    preferences: UserPreferences,
    count: int,
    filters_relaxed: bool,
) -> str:
    area_part = f" ({preferences.area})" if preferences.area else ""
    if count == 0:
        return (
            f"No restaurants found in {preferences.location}{area_part} for "
            f"{preferences.cuisine} cuisine with your current filters. "
            f"Try broadening your budget or rating."
        )
    relaxed_note = " Some filters were relaxed to find matches." if filters_relaxed else ""
    return (
        f"Found {count} top {preferences.cuisine} restaurant{'s' if count != 1 else ''} "
        f"in {preferences.location}{area_part} within your ₹{preferences.max_budget} "
        f"budget and minimum {preferences.min_rating} rating.{relaxed_note}"
    )
