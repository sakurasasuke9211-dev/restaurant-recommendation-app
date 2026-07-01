import json
import re
from dataclasses import dataclass, field

from src.phase1.constants import (
    BANGALORE_VARIANTS,
    CITY_ALIASES,
    GLOBAL_BUDGET_THRESHOLDS,
    PRICE_RANGE_HIGH,
    PRICE_RANGE_LOW,
    PRICE_RANGE_MEDIUM,
)


@dataclass
class CleanedRestaurant:
    name: str
    city: str
    area: str | None
    address: str | None
    cuisines: list[str]
    cost_for_two: int | None
    price_range: str
    rating: float | None
    votes: int
    restaurant_type: str | None
    online_order: bool
    book_table: bool
    popular_dishes: list[str]


@dataclass
class IngestionStats:
    records_loaded: int = 0
    records_skipped: int = 0
    records_deduplicated: int = 0
    null_rating_count: int = 0
    null_cost_count: int = 0
    errors: list[str] = field(default_factory=list)


def parse_rating(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"-", "NEW", "new", "None", "nan"}:
        return None
    match = re.search(r"(\d+\.?\d*)", text)
    if not match:
        return None
    rating = float(match.group(1))
    if rating > 5.0:
        return None
    return round(rating, 1)


def parse_cost(value: str | int | float | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"-", "None", "nan"}:
        return None
    text = re.sub(r"[₹$,]", "", text).strip()
    range_match = re.match(r"(\d+)\s*[-–]\s*(\d+)", text)
    if range_match:
        low, high = int(range_match.group(1)), int(range_match.group(2))
        return (low + high) // 2
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    return int(digits)


def parse_boolean(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"yes", "true", "1"}


def parse_list_field(value: str | None) -> list[str]:
    if not value or str(value).strip() in {"", "[]", "None", "nan"}:
        return []
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text.replace("'", '"'))
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in text.split(",") if part.strip()]


def parse_cuisines(value: str | None) -> list[str]:
    cuisines = parse_list_field(value)
    if not cuisines:
        return ["Unknown"]
    return [c.strip() for c in cuisines if c.strip()]


def normalize_city_from_address(address: str | None, default: str = "Bangalore") -> str | None:
    if not address or not address.strip():
        return None
    address_lower = address.lower()
    for variant in BANGALORE_VARIANTS:
        if variant in address_lower:
            return "Bangalore"
    for alias, canonical in CITY_ALIASES.items():
        if alias.lower() in address_lower:
            return canonical
    last_segment = address.split(",")[-1].strip()
    if last_segment in CITY_ALIASES:
        return CITY_ALIASES[last_segment]
    if last_segment and last_segment not in {"India", "Karnataka", "Delivery Only"}:
        if re.match(r"^Bangalore\s*-\s*\d+$", last_segment, re.IGNORECASE):
            return "Bangalore"
    return default


def normalize_city(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    cleaned = value.strip()
    if cleaned in CITY_ALIASES:
        return CITY_ALIASES[cleaned]
    if cleaned.lower() in BANGALORE_VARIANTS:
        return "Bangalore"
    return cleaned


def classify_price_range_global(cost: int | None) -> str:
    if cost is None:
        return PRICE_RANGE_MEDIUM
    if cost <= GLOBAL_BUDGET_THRESHOLDS[PRICE_RANGE_LOW][1]:
        return PRICE_RANGE_LOW
    if cost <= GLOBAL_BUDGET_THRESHOLDS[PRICE_RANGE_MEDIUM][1]:
        return PRICE_RANGE_MEDIUM
    return PRICE_RANGE_HIGH


def compute_city_price_thresholds(
    costs_by_city: dict[str, list[int]],
) -> dict[str, tuple[int, int]]:
    thresholds: dict[str, tuple[int, int]] = {}
    for city, costs in costs_by_city.items():
        if len(costs) < 10:
            continue
        sorted_costs = sorted(costs)
        p33_idx = int(len(sorted_costs) * 0.33)
        p66_idx = int(len(sorted_costs) * 0.66)
        thresholds[city] = (sorted_costs[p33_idx], sorted_costs[p66_idx])
    return thresholds


def classify_price_range(
    cost: int | None,
    city: str,
    city_thresholds: dict[str, tuple[int, int]],
) -> str:
    if cost is None:
        return PRICE_RANGE_MEDIUM
    if city in city_thresholds:
        low_max, medium_max = city_thresholds[city]
        if cost <= low_max:
            return PRICE_RANGE_LOW
        if cost <= medium_max:
            return PRICE_RANGE_MEDIUM
        return PRICE_RANGE_HIGH
    return classify_price_range_global(cost)


def clean_name(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    return str(value).strip()


def map_raw_row(row: dict) -> CleanedRestaurant | None:
    name = clean_name(row.get("name"))
    address = row.get("address")
    if not name:
        return None

    city = normalize_city_from_address(address)
    if not city:
        return None

    area = row.get("location")
    if area:
        area = str(area).strip() or None

    cuisines = parse_cuisines(row.get("cuisines"))
    cost_for_two = parse_cost(row.get("approx_cost(for two people)"))
    rating = parse_rating(row.get("rate"))
    votes_raw = row.get("votes")
    try:
        votes = int(votes_raw) if votes_raw is not None else 0
    except (TypeError, ValueError):
        votes = 0

    restaurant_type = row.get("rest_type")
    if restaurant_type:
        restaurant_type = str(restaurant_type).strip() or None

    popular_dishes = parse_list_field(row.get("dish_liked"))

    return CleanedRestaurant(
        name=name,
        city=city,
        area=area,
        address=str(address).strip() if address else None,
        cuisines=cuisines,
        cost_for_two=cost_for_two,
        price_range=PRICE_RANGE_MEDIUM,
        rating=rating,
        votes=votes,
        restaurant_type=restaurant_type,
        online_order=parse_boolean(row.get("online_order")),
        book_table=parse_boolean(row.get("book_table")),
        popular_dishes=popular_dishes,
    )


def assign_price_ranges(
    restaurants: list[CleanedRestaurant],
) -> None:
    costs_by_city: dict[str, list[int]] = {}
    for restaurant in restaurants:
        if restaurant.cost_for_two is not None:
            costs_by_city.setdefault(restaurant.city, []).append(restaurant.cost_for_two)

    city_thresholds = compute_city_price_thresholds(costs_by_city)
    for restaurant in restaurants:
        restaurant.price_range = classify_price_range(
            restaurant.cost_for_two,
            restaurant.city,
            city_thresholds,
        )


def deduplicate_restaurants(
    restaurants: list[CleanedRestaurant],
) -> tuple[list[CleanedRestaurant], int]:
    seen: set[tuple[str, str, str | None]] = set()
    unique: list[CleanedRestaurant] = []
    duplicates = 0
    for restaurant in restaurants:
        key = (
            restaurant.name.lower(),
            restaurant.city.lower(),
            (restaurant.address or "").lower() or None,
        )
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(restaurant)
    return unique, duplicates


def serialize_json_list(items: list[str]) -> str:
    return json.dumps(items, ensure_ascii=False)


def to_db_dict(restaurant: CleanedRestaurant) -> dict:
    return {
        "name": restaurant.name,
        "city": restaurant.city,
        "area": restaurant.area,
        "address": restaurant.address,
        "cuisines": serialize_json_list(restaurant.cuisines),
        "cost_for_two": restaurant.cost_for_two,
        "price_range": restaurant.price_range,
        "rating": restaurant.rating,
        "votes": restaurant.votes,
        "restaurant_type": restaurant.restaurant_type,
        "online_order": restaurant.online_order,
        "book_table": restaurant.book_table,
        "popular_dishes": serialize_json_list(restaurant.popular_dishes)
        if restaurant.popular_dishes
        else None,
    }
