#!/usr/bin/env python3
"""Phase 1 ETL pipeline: load Zomato dataset from Hugging Face into SQLite."""

from __future__ import annotations

import argparse
import logging

from datasets import load_dataset
from sqlalchemy import delete

from src.config import DATASET_NAME, DATASET_SPLIT, DEFAULT_DB_PATH
from src.phase1.database import drop_all, get_session, init_db
from src.phase1.loader import RestaurantRepository
from src.phase1.preprocessor import (
    IngestionStats,
    assign_price_ranges,
    deduplicate_restaurants,
    map_raw_row,
    to_db_dict,
)
from src.phase1.schema import IngestionLog, Restaurant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_hf_dataset():
    logger.info("Loading dataset '%s' (split=%s) from Hugging Face...", DATASET_NAME, DATASET_SPLIT)
    return load_dataset(DATASET_NAME, split=DATASET_SPLIT)


def transform_rows(rows, stats: IngestionStats) -> list:
    cleaned = []
    for row in rows:
        try:
            record = map_raw_row(dict(row))
            if record is None:
                stats.records_skipped += 1
                continue
            if record.rating is None:
                stats.null_rating_count += 1
            if record.cost_for_two is None:
                stats.null_cost_count += 1
            cleaned.append(record)
        except Exception as exc:
            stats.records_skipped += 1
            stats.errors.append(str(exc))
            if len(stats.errors) <= 10:
                logger.warning("Row transform error: %s", exc)
    return cleaned


def persist_restaurants(restaurants: list, stats: IngestionStats) -> None:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    with get_session() as session:
        session.execute(delete(Restaurant))
        session.execute(delete(IngestionLog))

        batch_size = 500
        for i in range(0, len(restaurants), batch_size):
            batch = restaurants[i : i + batch_size]
            session.bulk_insert_mappings(Restaurant, [to_db_dict(r) for r in batch])

        stats.records_loaded = len(restaurants)

        price_stats = {"low": 0, "medium": 0, "high": 0}
        cities: set[str] = set()
        for r in restaurants:
            cities.add(r.city)
            price_stats[r.price_range] = price_stats.get(r.price_range, 0) + 1

        log = IngestionLog(
            dataset_name=DATASET_NAME,
            records_loaded=stats.records_loaded,
            records_skipped=stats.records_skipped,
            records_deduplicated=stats.records_deduplicated,
            cities_count=len(cities),
            null_rating_count=stats.null_rating_count,
            null_cost_count=stats.null_cost_count,
            price_range_low=price_stats.get("low", 0),
            price_range_medium=price_stats.get("medium", 0),
            price_range_high=price_stats.get("high", 0),
            errors="\n".join(stats.errors[:50]) if stats.errors else None,
        )
        session.add(log)


def print_report(stats: IngestionStats, restaurants: list) -> None:
    logger.info("=" * 60)
    logger.info("INGESTION REPORT")
    logger.info("=" * 60)
    logger.info("Database path: %s", DEFAULT_DB_PATH)
    logger.info("Records loaded: %d", stats.records_loaded)
    logger.info("Records skipped: %d", stats.records_skipped)
    logger.info("Records deduplicated: %d", stats.records_deduplicated)
    logger.info("Null ratings: %d", stats.null_rating_count)
    logger.info("Null costs: %d", stats.null_cost_count)

    price_counts: dict[str, int] = {}
    city_counts: dict[str, int] = {}
    for r in restaurants:
        price_counts[r.price_range] = price_counts.get(r.price_range, 0) + 1
        city_counts[r.city] = city_counts.get(r.city, 0) + 1

    logger.info("Price range distribution:")
    for tier in ("low", "medium", "high"):
        logger.info("  %s: %d", tier, price_counts.get(tier, 0))

    logger.info("Top cities:")
    for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info("  %s: %d", city, count)

    with get_session() as session:
        repo = RestaurantRepository(session)
        bangalore_4plus = repo.count_by_filters("Bangalore", min_rating=4.0)
        logger.info("Validation — Bangalore rating >= 4.0: %d", bangalore_4plus)

    if stats.errors:
        logger.warning("Transform errors (first 5): %s", stats.errors[:5])


def run_ingestion(reset: bool = True) -> IngestionStats:
    stats = IngestionStats()
    dataset = load_hf_dataset()
    logger.info("Raw rows: %d", len(dataset))

    cleaned = transform_rows(dataset, stats)
    logger.info("Cleaned rows: %d", len(cleaned))

    assign_price_ranges(cleaned)
    unique, dup_count = deduplicate_restaurants(cleaned)
    stats.records_deduplicated = dup_count
    logger.info("After deduplication: %d (removed %d)", len(unique), dup_count)

    if reset:
        drop_all()
    persist_restaurants(unique, stats)
    print_report(stats, unique)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Zomato dataset into SQLite")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not drop existing tables before ingestion",
    )
    args = parser.parse_args()
    run_ingestion(reset=not args.no_reset)


if __name__ == "__main__":
    main()
