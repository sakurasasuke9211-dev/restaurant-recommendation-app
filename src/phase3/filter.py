import re
from dataclasses import dataclass, field

from src.config import (
    BUDGET_RELAXATION_INCREMENT,
    BUDGET_RELAXATION_STEPS,
    LLM_CANDIDATE_COUNT,
    MAX_RECOMMENDATIONS,
)
from src.phase1.loader import RestaurantRepository, deserialize_json_list
from src.phase1.schema import Restaurant
from src.phase2.api.schemas import UserPreferences

PHRASE_RULES: list[tuple[str, list[str]]] = [
    ("family friendly", ["casual dining", "family"]),
    ("quick service", ["quick bites", "fast food"]),
]

BOOLEAN_PHRASES = {
    "online order": "online_order",
    "online ordering": "online_order",
    "book table": "book_table",
    "table booking": "book_table",
}


@dataclass
class FilterResult:
    candidates: list[Restaurant]
    filters_relaxed: bool = False
    relaxation_steps: list[str] = field(default_factory=list)
    budget_blocked: bool = False


class FilterService:
    def __init__(self, repo: RestaurantRepository) -> None:
        self._repo = repo

    def get_shortlist(self, preferences: UserPreferences) -> FilterResult:
        relaxation_steps: list[str] = []
        merged: list[Restaurant] = []
        seen_ids: set[int] = set()

        def add_candidates(restaurants: list[Restaurant]) -> None:
            for restaurant in restaurants:
                if restaurant.id not in seen_ids:
                    seen_ids.add(restaurant.id)
                    merged.append(restaurant)

        def enough() -> bool:
            return len(merged) >= MAX_RECOMMENDATIONS

        with_budget = self._query(
            preferences,
            max_budget=preferences.max_budget,
            min_rating=preferences.min_rating,
            cuisine=preferences.cuisine,
            area=preferences.area,
        )
        without_budget = self._query(
            preferences,
            max_budget=None,
            min_rating=preferences.min_rating,
            cuisine=preferences.cuisine,
            area=preferences.area,
        )
        budget_blocked = len(with_budget) == 0 and len(without_budget) > 0

        strict = with_budget
        add_candidates(strict)
        if enough():
            return FilterResult(
                candidates=self._cap_candidates(merged, preferences),
                filters_relaxed=False,
                budget_blocked=budget_blocked,
            )

        max_relaxed_budget = preferences.max_budget
        lowered_rating = preferences.min_rating

        for step in range(1, BUDGET_RELAXATION_STEPS + 1):
            max_relaxed_budget = preferences.max_budget + BUDGET_RELAXATION_INCREMENT * step
            if max_relaxed_budget > 10000:
                break
            relaxed_budget = self._query(
                preferences,
                max_budget=max_relaxed_budget,
                min_rating=preferences.min_rating,
                cuisine=preferences.cuisine,
                area=preferences.area,
            )
            if relaxed_budget:
                if "max_budget" not in relaxation_steps:
                    relaxation_steps.append("max_budget")
                add_candidates(relaxed_budget)
                if enough():
                    break

        if not enough():
            lowered_rating = max(preferences.min_rating - 0.5, 0.0)
            if lowered_rating < preferences.min_rating:
                relaxed_rating = self._query(
                    preferences,
                    max_budget=max_relaxed_budget,
                    min_rating=lowered_rating,
                    cuisine=preferences.cuisine,
                    area=preferences.area,
                )
                if relaxed_rating:
                    relaxation_steps.append("min_rating")
                    add_candidates(relaxed_rating)

        if not enough():
            relaxed_cuisine = self._query(
                preferences,
                max_budget=max_relaxed_budget,
                min_rating=lowered_rating if "min_rating" in relaxation_steps else preferences.min_rating,
                cuisine=None,
                area=preferences.area,
            )
            if relaxed_cuisine:
                relaxation_steps.append("cuisine")
                add_candidates(relaxed_cuisine)

        if not enough() and preferences.area:
            city_wide = self._query(
                preferences,
                max_budget=max_relaxed_budget,
                min_rating=lowered_rating if "min_rating" in relaxation_steps else preferences.min_rating,
                cuisine=preferences.cuisine,
                area=None,
            )
            if city_wide:
                relaxation_steps.append("area")
                add_candidates(city_wide)

        if not enough():
            city_only = list(
                self._repo.get_by_filters(
                    city=preferences.location,
                    limit=LLM_CANDIDATE_COUNT * 3,
                )
            )
            if city_only:
                relaxation_steps.append("city_only")
                add_candidates(city_only)

        return FilterResult(
            candidates=self._cap_candidates(merged, preferences),
            filters_relaxed=bool(relaxation_steps),
            relaxation_steps=relaxation_steps,
            budget_blocked=budget_blocked,
        )

    def _cap_candidates(
        self,
        restaurants: list[Restaurant],
        preferences: UserPreferences,
    ) -> list[Restaurant]:
        return self._rank_by_keywords(restaurants, preferences)[:LLM_CANDIDATE_COUNT]

    def _query(
        self,
        preferences: UserPreferences,
        *,
        cuisine: str | None,
        min_rating: float | None,
        max_budget: int | None = None,
        area: str | None = None,
    ) -> list[Restaurant]:
        return list(
            self._repo.get_by_filters(
                city=preferences.location,
                area=area if area is not None else preferences.area,
                cuisine=cuisine,
                min_rating=min_rating,
                max_budget=max_budget,
                limit=LLM_CANDIDATE_COUNT * 3,
            )
        )

    def _rank_by_keywords(
        self,
        restaurants: list[Restaurant],
        preferences: UserPreferences,
    ) -> list[Restaurant]:
        if not preferences.additional_preferences:
            return restaurants
        scored = [
            (score_keyword_match(restaurant, preferences.additional_preferences), restaurant)
            for restaurant in restaurants
        ]
        scored.sort(
            key=lambda item: (
                -item[0],
                -(item[1].rating or 0),
                -item[1].votes,
            )
        )
        return [restaurant for _, restaurant in scored]


def score_keyword_match(restaurant: Restaurant, additional_preferences: str) -> int:
    text = additional_preferences.lower()
    score = 0
    rest_type = (restaurant.restaurant_type or "").lower()
    dishes = " ".join(deserialize_json_list(restaurant.popular_dishes)).lower()

    for phrase, type_keywords in PHRASE_RULES:
        if phrase in text and any(kw in rest_type for kw in type_keywords):
            score += 2

    for phrase, attr in BOOLEAN_PHRASES.items():
        if phrase in text and getattr(restaurant, attr):
            score += 2

    for token in _extract_tokens(text):
        if len(token) < 3:
            continue
        if token in rest_type or token in dishes:
            score += 1
        if token in (restaurant.cuisines or "").lower():
            score += 1

    return score


def _extract_tokens(text: str) -> list[str]:
    normalized = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = normalized.split()
    skip = {
        "and", "or", "the", "with", "for", "a", "an", "in", "on", "at",
        "family", "friendly", "quick", "service", "order", "book", "table",
        "online", "ordering", "booking",
    }
    return [token for token in tokens if token not in skip]
