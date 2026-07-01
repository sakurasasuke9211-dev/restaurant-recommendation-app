from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    area: Mapped[str | None] = mapped_column(String(150))
    address: Mapped[str | None] = mapped_column(Text)
    cuisines: Mapped[str] = mapped_column(Text, nullable=False)
    cost_for_two: Mapped[int | None] = mapped_column(Integer)
    price_range: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rating: Mapped[float | None] = mapped_column(Float, index=True)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    restaurant_type: Mapped[str | None] = mapped_column(String(100))
    online_order: Mapped[bool] = mapped_column(Boolean, default=False)
    book_table: Mapped[bool] = mapped_column(Boolean, default=False)
    popular_dishes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_restaurants_city_rating", "city", "rating"),
    )


class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    records_loaded: Mapped[int] = mapped_column(Integer, nullable=False)
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_deduplicated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cities_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    null_rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    null_cost_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_range_low: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_range_medium: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_range_high: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[str | None] = mapped_column(Text)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
