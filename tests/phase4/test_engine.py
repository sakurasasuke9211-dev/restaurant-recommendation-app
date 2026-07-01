import json

from unittest.mock import patch



import pytest



from src.phase1.schema import Restaurant

from src.phase2.api.schemas import RecommendationItem, UserPreferences

from src.phase3.llm import LLMResponseError

from src.phase4.engine import RecommendationEngine, sort_recommendations_by_rating, validate_and_normalize_llm_output



SAMPLE_LLM = {

    "summary": "Top Italian spots in Bangalore.",

    "recommendations": [

        {

            "rank": 1,

            "restaurant_id": 10,

            "restaurant_name": "Cafesta",

            "explanation": "Great Italian cafe with strong ratings.",

        },

        {

            "rank": 2,

            "restaurant_id": 11,

            "restaurant_name": "Smacznego",

            "explanation": "",

        },

    ],

}





def _restaurant(rid: int, **kwargs) -> Restaurant:

    defaults = dict(

        id=rid,

        name=f"R{rid}",

        city="Bangalore",

        area="HSR",

        cuisines='["Italian"]',

        cost_for_two=700,

        price_range="medium",

        rating=4.3,

        votes=300,

        restaurant_type="Casual Dining",

        online_order=True,

        book_table=False,

        popular_dishes='["Pasta"]',

    )

    defaults.update(kwargs)

    return Restaurant(**defaults)





def _prefs() -> UserPreferences:

    return UserPreferences(

        location="Bangalore",

        max_budget=800,

        cuisine="Italian",

        min_rating=4.0,

    )





class TestValidateAndNormalize:

    def test_accepts_valid_entries(self):

        candidates = {_restaurant(10), _restaurant(11)}

        candidate_map = {r.id: r for r in candidates}

        items = validate_and_normalize_llm_output(

            SAMPLE_LLM, candidate_map, _prefs(), max_results=5

        )

        assert len(items) == 2

        assert items[0].restaurant_id == 10

        assert items[0].area == "HSR"

        assert items[1].explanation



    def test_rejects_unknown_ids(self):

        candidate_map = {10: _restaurant(10)}

        data = {

            "summary": "x",

            "recommendations": [

                {"rank": 1, "restaurant_id": 99, "explanation": "bad id"}

            ],

        }

        items = validate_and_normalize_llm_output(data, candidate_map, _prefs(), 5)

        assert items == []



class TestSortRecommendationsByRating:

    def test_orders_highest_rating_first(self):

        items = [

            RecommendationItem(

                rank=1,

                restaurant_id=1,

                name="Low Rated",

                area="HSR",

                cuisines=["Italian"],

                rating=3.8,

                cost_for_two=500,

                price_range="low",

                explanation="A",

            ),

            RecommendationItem(

                rank=2,

                restaurant_id=2,

                name="Top Rated",

                area="HSR",

                cuisines=["Italian"],

                rating=4.9,

                cost_for_two=700,

                price_range="medium",

                explanation="B",

            ),

        ]

        sorted_items = sort_recommendations_by_rating(items)

        assert sorted_items[0].name == "Top Rated"

        assert sorted_items[0].rank == 1

        assert sorted_items[1].name == "Low Rated"

        assert sorted_items[1].rank == 2






class TestRecommendationEngine:

    @patch("src.phase4.engine.is_llm_available", return_value=False)

    def test_fallback_when_llm_disabled(self, _avail):

        engine = RecommendationEngine()

        candidates = [_restaurant(1), _restaurant(2, rating=4.8)]

        response = engine.run(_prefs(), candidates, filters_relaxed=False, processing_time_ms=10)

        assert response.meta.llm_used is False

        assert len(response.recommendations) == 2

        assert response.recommendations[0].rating == 4.8



    @patch("src.phase4.engine.is_llm_available", return_value=True)

    @patch("src.phase4.engine.complete", return_value=json.dumps(SAMPLE_LLM))

    def test_groq_pipeline(self, _complete, _avail):

        engine = RecommendationEngine()

        candidates = [_restaurant(10), _restaurant(11), _restaurant(12, rating=4.0)]

        response = engine.run(

            _prefs(),

            candidates,

            filters_relaxed=False,

            processing_time_ms=50,

            relaxation_steps=["max_budget"],

        )

        assert response.meta.llm_used is True

        assert response.meta.relaxation_steps == ["Budget limit increased"]

        assert response.summary.startswith("Top Italian")

        assert len(response.recommendations) >= 2



    @patch("src.phase4.engine.is_llm_available", return_value=True)

    @patch(

        "src.phase4.engine.complete",

        return_value=json.dumps(

            {

                "summary": "One pick from Groq.",

                "recommendations": [

                    {

                        "rank": 1,

                        "restaurant_id": 10,

                        "restaurant_name": "Cafesta",

                        "explanation": "Best Italian option.",

                    }

                ],

            }

        ),

    )

    def test_supplements_to_five_when_llm_returns_one(self, _complete, _avail):

        engine = RecommendationEngine()

        candidates = [_restaurant(i) for i in range(10, 15)]

        response = engine.run(_prefs(), candidates, filters_relaxed=False, processing_time_ms=50)

        assert response.meta.llm_used is True

        assert len(response.recommendations) == 5

        ratings = [item.rating for item in response.recommendations if item.rating is not None]

        assert ratings == sorted(ratings, reverse=True)

        assert len({item.restaurant_id for item in response.recommendations}) == 5



    @patch("src.phase4.engine.is_llm_available", return_value=True)

    @patch("src.phase4.engine.complete", side_effect=LLMResponseError("bad json"))

    def test_falls_back_on_llm_error(self, _complete, _avail):

        engine = RecommendationEngine()

        candidates = [_restaurant(1), _restaurant(2)]

        response = engine.run(_prefs(), candidates, filters_relaxed=False, processing_time_ms=5)

        assert response.meta.llm_used is False

        assert len(response.recommendations) == 2


