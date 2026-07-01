import re

from src.phase1.constants import ALL_AREAS_LABEL, AREA_ALIASES, CITY_ALIASES

_HTML_OR_SCRIPT_PATTERN = re.compile(r"<[^>]+>|script", re.IGNORECASE)


class CityNotFoundError(Exception):
    def __init__(self, city: str) -> None:
        self.city = city
        super().__init__(f"City '{city}' not found. See /api/v1/meta/cities.")


def normalize_location(location: str) -> str:
    cleaned = location.strip()
    if cleaned in CITY_ALIASES:
        return CITY_ALIASES[cleaned]
    for alias, canonical in CITY_ALIASES.items():
        if alias.lower() == cleaned.lower():
            return canonical
    return cleaned


def normalize_area(area: str | None) -> str | None:
    if area is None:
        return None
    cleaned = area.strip()
    if not cleaned or cleaned.lower() == ALL_AREAS_LABEL.lower():
        return None
    if cleaned in AREA_ALIASES:
        return AREA_ALIASES[cleaned]
    for alias, canonical in AREA_ALIASES.items():
        if alias.lower() == cleaned.lower():
            return canonical
    return cleaned


def normalize_min_rating(value: float) -> float:
    return round(value, 1)


def sanitize_additional_preferences(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if _HTML_OR_SCRIPT_PATTERN.search(cleaned):
        raise ValueError("Additional preferences must not contain HTML or script tags")
    return cleaned


def normalize_request(
    location: str,
    max_budget: int,
    cuisine: str,
    min_rating: float,
    additional_preferences: str | None,
    area: str | None = None,
):
    from src.phase2.api.schemas import UserPreferences

    normalized_location = normalize_location(location)
    normalized_area = normalize_area(area)
    normalized_cuisine = cuisine.strip()
    normalized_rating = normalize_min_rating(min_rating)
    normalized_additional = sanitize_additional_preferences(additional_preferences)

    return UserPreferences(
        location=normalized_location,
        max_budget=max_budget,
        cuisine=normalized_cuisine,
        min_rating=normalized_rating,
        area=normalized_area,
        additional_preferences=normalized_additional,
    )
