import json

import tempfile

from pathlib import Path



import pytest

from sqlalchemy import create_engine, select

from sqlalchemy.orm import sessionmaker



from src.phase1.preprocessor import CleanedRestaurant, to_db_dict

from src.phase1.schema import Base, Restaurant

from src.phase2.api.schemas import UserPreferences

from src.phase3.filter import FilterService, score_keyword_match

from src.phase1.loader import RestaurantRepository





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





@pytest.fixture

def filter_session():

    tmp = tempfile.mkdtemp()

    db_path = Path(tmp) / "filter_test.db"

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    session = Session()



    session.add(Restaurant(**to_db_dict(_make_restaurant(name="Italian Place", rating=4.5))))

    session.add(

        Restaurant(

            name="Quick Bites Spot",

            city="Bangalore",

            area="Indiranagar",

            address="Indiranagar, Bangalore",

            cuisines=json.dumps(["Fast Food"]),

            cost_for_two=300,

            price_range="low",

            rating=4.0,

            votes=200,

            restaurant_type="Quick Bites",

            online_order=True,

            book_table=False,

            popular_dishes=json.dumps(["Burger"]),

        )

    )

    session.add(

        Restaurant(

            name="Premium Italian",

            city="Bangalore",

            area="Lavelle Road",

            address="Lavelle Road, Bangalore",

            cuisines=json.dumps(["Italian"]),

            cost_for_two=1200,

            price_range="high",

            rating=4.8,

            votes=900,

            restaurant_type="Fine Dining",

            online_order=True,

            book_table=True,

            popular_dishes=json.dumps(["Pasta"]),

        )

    )

    session.commit()

    yield session

    session.close()

    engine.dispose()





def _prefs(**kwargs) -> UserPreferences:

    defaults = {

        "location": "Bangalore",

        "max_budget": 800,

        "cuisine": "Italian",

        "min_rating": 4.0,

        "additional_preferences": None,

        "area": None,

    }

    defaults.update(kwargs)

    return UserPreferences(**defaults)





class TestFilterService:

    def test_strict_filter_returns_matches(self, filter_session):

        repo = RestaurantRepository(filter_session)

        service = FilterService(repo)

        result = service.get_shortlist(_prefs())

        assert len(result.candidates) >= 1

        assert any("Italian" in r.cuisines for r in result.candidates)

        assert result.candidates[0].name == "Italian Place"



    def test_area_filter(self, filter_session):

        repo = RestaurantRepository(filter_session)

        service = FilterService(repo)

        result = service.get_shortlist(_prefs(area="Indiranagar", max_budget=500, cuisine="Fast Food"))

        assert len(result.candidates) >= 1

        assert result.candidates[0].name == "Quick Bites Spot"



    def test_relaxation_when_no_strict_matches(self, filter_session):

        repo = RestaurantRepository(filter_session)

        service = FilterService(repo)

        result = service.get_shortlist(_prefs(max_budget=300, min_rating=4.0))

        assert result.filters_relaxed is True

        assert "max_budget" in result.relaxation_steps

        assert len(result.candidates) >= 1

        assert result.budget_blocked is True



    def test_budget_blocked_when_nothing_in_budget(self, filter_session):

        repo = RestaurantRepository(filter_session)

        service = FilterService(repo)

        result = service.get_shortlist(_prefs(max_budget=100, min_rating=4.0))

        assert result.budget_blocked is True

        assert len(result.candidates) >= 1



    def test_budget_not_blocked_when_matches_exist(self, filter_session):

        repo = RestaurantRepository(filter_session)

        service = FilterService(repo)

        result = service.get_shortlist(_prefs(max_budget=800))

        assert result.budget_blocked is False



    def test_keyword_scoring_prefers_family_friendly(self, filter_session):

        repo = RestaurantRepository(filter_session)

        service = FilterService(repo)

        result = service.get_shortlist(

            _prefs(additional_preferences="family friendly, casual dining")

        )

        assert result.candidates[0].restaurant_type == "Casual Dining"



    def test_quick_service_keyword(self, filter_session):

        repo = RestaurantRepository(filter_session)

        restaurant = filter_session.scalars(

            select(Restaurant).where(Restaurant.name == "Quick Bites Spot")

        ).one()

        score = score_keyword_match(restaurant, "quick service")

        assert score >= 2





class TestScoreKeywordMatch:

    def test_online_order_phrase(self):

        restaurant = Restaurant(

            name="Test",

            city="Bangalore",

            cuisines='["Indian"]',

            price_range="low",

            online_order=True,

            book_table=False,

        )

        assert score_keyword_match(restaurant, "online order") >= 2


