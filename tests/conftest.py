import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.phase2.api.dependencies import get_db
from src.phase1.preprocessor import CleanedRestaurant, to_db_dict
from src.phase1.schema import Base, Restaurant
from src.phase2.main import app


def _make_restaurant(**kwargs) -> CleanedRestaurant:
    defaults = {
        "name": "Truffles",
        "city": "Bangalore",
        "area": "St Marks",
        "address": "St Marks Road, Bangalore",
        "cuisines": ["Italian", "American"],
        "cost_for_two": 700,
        "price_range": "medium",
        "rating": 4.6,
        "votes": 500,
        "restaurant_type": "Casual Dining",
        "online_order": True,
        "book_table": True,
        "popular_dishes": ["Burger"],
    }
    defaults.update(kwargs)
    return CleanedRestaurant(**defaults)


@pytest.fixture(autouse=True)
def disable_live_llm_in_unit_tests():
    """Keep API unit tests deterministic when a real GROQ_API_KEY is in .env."""
    with patch("src.phase4.engine.is_llm_available", return_value=False):
        yield


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test_api.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestSession()

    session.add(Restaurant(**to_db_dict(_make_restaurant())))
    session.add(
        Restaurant(
            name="Meghana Foods",
            city="Bangalore",
            area="Indiranagar",
            address="Indiranagar, Bangalore",
            cuisines=json.dumps(["Biryani", "South Indian"]),
            cost_for_two=400,
            price_range="low",
            rating=4.2,
            votes=1200,
            restaurant_type="Quick Bites",
            online_order=True,
            book_table=False,
            popular_dishes=json.dumps(["Biryani"]),
        )
    )
    session.add(
        Restaurant(
            name="Toscano",
            city="Bangalore",
            area="Lavelle Road",
            address="Lavelle Road, Bangalore",
            cuisines=json.dumps(["Italian", "Pizza"]),
            cost_for_two=900,
            price_range="high",
            rating=4.4,
            votes=800,
            restaurant_type="Casual Dining",
            online_order=True,
            book_table=True,
            popular_dishes=json.dumps(["Pizza"]),
        )
    )
    session.commit()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    session.close()
    engine.dispose()
