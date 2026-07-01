import json
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.phase1.schema import Restaurant


def deserialize_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return [value]


class RestaurantRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, restaurant_id: int) -> Restaurant | None:
        return self._session.get(Restaurant, restaurant_id)

    def get_cities(self) -> list[str]:
        stmt = (
            select(Restaurant.city)
            .distinct()
            .order_by(Restaurant.city)
        )
        return list(self._session.scalars(stmt))

    def get_cuisines(self, city: str | None = None) -> list[str]:
        stmt = select(Restaurant.cuisines)
        if city:
            stmt = stmt.where(Restaurant.city == city)
        cuisine_set: set[str] = set()
        for raw in self._session.scalars(stmt):
            for cuisine in deserialize_json_list(raw):
                cuisine_set.add(cuisine.strip())
        return sorted(cuisine_set)

    def get_areas(self, city: str) -> list[str]:
        from src.phase1.constants import ALL_AREAS_LABEL

        stmt = (
            select(Restaurant.area, func.count())
            .where(Restaurant.city == city, Restaurant.area.is_not(None))
            .group_by(Restaurant.area)
            .order_by(func.count().desc(), Restaurant.area)
        )
        areas = [row[0] for row in self._session.execute(stmt).all() if row[0]]
        return [ALL_AREAS_LABEL, *areas]

    def count_all(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Restaurant)) or 0

    def count_by_city(self, city: str) -> int:
        stmt = select(func.count()).select_from(Restaurant).where(Restaurant.city == city)
        return self._session.scalar(stmt) or 0

    def count_by_filters(
        self,
        city: str,
        cuisine: str | None = None,
        min_rating: float | None = None,
        price_range: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Restaurant).where(Restaurant.city == city)
        stmt = _apply_filters(stmt, cuisine, min_rating, price_range, None, None, None)
        return self._session.scalar(stmt) or 0

    def get_by_filters(
        self,
        city: str,
        cuisine: str | None = None,
        min_rating: float | None = None,
        price_range: str | None = None,
        price_ranges: list[str] | None = None,
        area: str | None = None,
        max_budget: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Restaurant]:
        stmt = select(Restaurant).where(Restaurant.city == city)
        stmt = _apply_filters(
            stmt,
            cuisine,
            min_rating,
            price_range,
            price_ranges,
            area,
            max_budget,
        )
        stmt = (
            stmt.order_by(Restaurant.rating.desc().nullslast(), Restaurant.votes.desc())
            .limit(limit)
            .offset(offset)
        )
        return self._session.scalars(stmt).all()

    def get_city_stats(self) -> list[tuple[str, int]]:
        stmt = (
            select(Restaurant.city, func.count())
            .group_by(Restaurant.city)
            .order_by(func.count().desc())
        )
        return list(self._session.execute(stmt).all())

    def get_price_range_stats(self) -> list[tuple[str, int]]:
        stmt = (
            select(Restaurant.price_range, func.count())
            .group_by(Restaurant.price_range)
            .order_by(Restaurant.price_range)
        )
        return list(self._session.execute(stmt).all())


def _apply_filters(
    stmt,
    cuisine: str | None,
    min_rating: float | None,
    price_range: str | None,
    price_ranges: list[str] | None = None,
    area: str | None = None,
    max_budget: int | None = None,
):
    if min_rating is not None:
        stmt = stmt.where(Restaurant.rating.is_not(None), Restaurant.rating >= min_rating)
    if price_ranges:
        stmt = stmt.where(Restaurant.price_range.in_(price_ranges))
    elif price_range:
        stmt = stmt.where(Restaurant.price_range == price_range)
    if max_budget is not None:
        stmt = stmt.where(
            Restaurant.cost_for_two.is_not(None),
            Restaurant.cost_for_two <= max_budget,
        )
    if area:
        stmt = stmt.where(Restaurant.area == area)
    if cuisine:
        stmt = stmt.where(Restaurant.cuisines.ilike(f"%{cuisine}%"))
    return stmt
