from src.phase1.schema import Restaurant

from src.phase2.api.schemas import UserPreferences

from src.phase3.prompt import build_prompt, estimate_token_count, restaurant_to_llm_dict





def _restaurant() -> Restaurant:

    return Restaurant(

        id=1,

        name="Truffles",

        city="Bangalore",

        area="St Marks",

        cuisines='["Italian", "American"]',

        cost_for_two=700,

        price_range="medium",

        rating=4.6,

        votes=500,

        restaurant_type="Casual Dining",

        online_order=True,

        book_table=True,

        popular_dishes='["Burger", "Pasta"]',

    )





class TestPromptBuilder:

    def test_restaurant_to_llm_dict(self):

        data = restaurant_to_llm_dict(_restaurant())

        assert data["restaurant_id"] == 1

        assert data["id"] == 1

        assert data["area"] == "St Marks"

        assert "Italian" in data["cuisines"]

        assert data["online_order"] is True



    def test_build_prompt_structure(self):

        prefs = UserPreferences(

            location="Bangalore",

            max_budget=800,

            cuisine="Italian",

            min_rating=4.0,

            area="HSR",

            additional_preferences="family friendly",

        )

        messages = build_prompt(prefs, [_restaurant()])

        assert len(messages) == 2

        assert messages[0]["role"] == "system"

        assert messages[1]["role"] == "user"

        assert "Bangalore" in messages[1]["content"]

        assert "₹800" in messages[1]["content"]

        assert "HSR" in messages[1]["content"]

        assert "Truffles" in messages[1]["content"]



    def test_token_estimate_under_limit_for_shortlist(self):

        prefs = UserPreferences(

            location="Bangalore",

            max_budget=800,

            cuisine="Italian",

            min_rating=4.0,

        )

        candidates = [_restaurant() for _ in range(20)]

        messages = build_prompt(prefs, candidates)

        assert estimate_token_count(messages) < 4000



    def test_user_prompt_contains_json_schema(self):

        prefs = UserPreferences(

            location="Bangalore",

            max_budget=800,

            cuisine="Italian",

            min_rating=4.0,

        )

        messages = build_prompt(prefs, [_restaurant()])

        assert '"summary"' in messages[1]["content"]

        assert "restaurant_id" in messages[1]["content"]


