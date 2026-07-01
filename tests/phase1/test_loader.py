import json
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.phase1.loader import RestaurantRepository
from src.phase1.preprocessor import CleanedRestaurant, to_db_dict
from src.phase1.schema import Base, Restaurant


def _make_restaurant(**kwargs) -> CleanedRestaurant:
    defaults = {
        "name": "Truffles",
        "city": "Bangalore",
        "area": "St Marks",
        "address": "St Marks Road, Bangalore",
        "cuisines": ["Italian", "American"],
        "cost_for_two": 900,
        "price_range": "high",
        "rating": 4.6,
        "votes": 500,
        "restaurant_type": "Casual Dining",
        "online_order": True,
        "book_table": True,
        "popular_dishes": ["Burger"],
    }
    defaults.update(kwargs)
    return CleanedRestaurant(**defaults)


@pytest.fixture
def db_session():
    tmp = tempfile.mkdtemp()
    db_path = Path(tmp) / "test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(Restaurant(**to_db_dict(_make_restaurant())))
    session.add(
        Restaurant(
            name="Meghana",
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
    session.commit()
    yield session
    session.close()
    engine.dispose()


class TestRestaurantRepository:
    def test_get_cities(self, db_session):
        repo = RestaurantRepository(db_session)
        assert "Bangalore" in repo.get_cities()

    def test_get_cuisines(self, db_session):
        repo = RestaurantRepository(db_session)
        cuisines = repo.get_cuisines(city="Bangalore")
        assert "Italian" in cuisines
        assert "Biryani" in cuisines

    def test_count_by_filters(self, db_session):
        repo = RestaurantRepository(db_session)
        assert repo.count_by_filters("Bangalore", min_rating=4.0) == 2
        assert repo.count_by_filters("Bangalore", cuisine="Italian", min_rating=4.0) == 1
        assert repo.count_by_filters("Bangalore", price_range="low") == 1

    def test_get_by_filters(self, db_session):
        repo = RestaurantRepository(db_session)
        results = repo.get_by_filters("Bangalore", min_rating=4.0, limit=10)
        assert len(results) == 2
        assert results[0].rating >= 4.0
