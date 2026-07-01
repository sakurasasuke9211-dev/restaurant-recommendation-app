import pytest



from src.phase1.schema import Restaurant

from src.phase2.api.schemas import UserPreferences

from src.phase4.ranker import (

    build_fallback_recommendations,

    rank_candidates,

    score_restaurant,

)





def _restaurant(**kwargs) -> Restaurant:

    defaults = {

        "id": 1,

        "name": "Alpha",

        "city": "Bangalore",

        "area": "HSR",

        "cuisines": '["Italian"]',

        "cost_for_two": 600,

        "price_range": "medium",

        "rating": 4.5,

        "votes": 1000,

        "restaurant_type": "Casual Dining",

        "online_order": True,

        "book_table": True,

        "popular_dishes": '["Pasta"]',

    }

    defaults.update(kwargs)

    return Restaurant(**defaults)





def _prefs(**kwargs) -> UserPreferences:

    defaults = {

        "location": "Bangalore",

        "max_budget": 800,

        "cuisine": "Italian",

        "min_rating": 4.0,

        "additional_preferences": "family friendly",

    }

    defaults.update(kwargs)

    return UserPreferences(**defaults)





class TestScoreRestaurant:

    def test_higher_rating_scores_higher(self):

        prefs = _prefs()

        high = _restaurant(id=1, rating=4.8, votes=500)

        low = _restaurant(id=2, rating=3.5, votes=500)

        assert score_restaurant(high, prefs, 1000) > score_restaurant(low, prefs, 1000)



    def test_cuisine_match_adds_score(self):

        prefs = _prefs(cuisine="Italian")

        match = _restaurant(id=1, cuisines='["Italian", "Pizza"]')

        miss = _restaurant(id=2, cuisines='["Chinese"]')

        assert score_restaurant(match, prefs, 100) > score_restaurant(miss, prefs, 100)



    def test_over_budget_scores_lower(self):

        prefs = _prefs(max_budget=500)

        within = _restaurant(id=1, cost_for_two=400)

        over = _restaurant(id=2, cost_for_two=900, rating=4.9)

        assert score_restaurant(within, prefs, 100) > score_restaurant(over, prefs, 100)





class TestRankCandidates:

    def test_orders_by_score(self):

        prefs = _prefs()

        candidates = [

            _restaurant(id=1, rating=4.0, votes=100),

            _restaurant(id=2, rating=4.8, votes=900),

            _restaurant(id=3, rating=4.2, votes=400),

        ]

        ranked = rank_candidates(candidates, prefs)

        assert ranked[0].id == 2





class TestFallbackRecommendations:

    def test_builds_ranked_items(self):

        prefs = _prefs()

        candidates = [

            _restaurant(id=1, rating=4.1),

            _restaurant(id=2, rating=4.7),

        ]

        items = build_fallback_recommendations(candidates, prefs, limit=2)

        assert len(items) == 2

        assert items[0].rank == 1

        assert items[0].restaurant_id == 2

        assert items[0].area == "HSR"

        assert "star" in items[0].explanation.lower() or "well-reviewed" in items[0].explanation



    def test_excludes_ids(self):

        prefs = _prefs()

        candidates = [_restaurant(id=1), _restaurant(id=2, rating=4.9)]

        items = build_fallback_recommendations(candidates, prefs, exclude_ids={2}, limit=1)

        assert len(items) == 1

        assert items[0].restaurant_id == 1


