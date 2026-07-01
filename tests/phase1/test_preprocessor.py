import pytest

from src.phase1.preprocessor import (
    assign_price_ranges,
    classify_price_range_global,
    deduplicate_restaurants,
    map_raw_row,
    normalize_city_from_address,
    parse_cost,
    parse_cuisines,
    parse_rating,
    to_db_dict,
)


class TestParseRating:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("4.1/5", 4.1),
            ("3.8 /5", 3.8),
            ("NEW", None),
            ("-", None),
            (None, None),
            ("4.6/5", 4.6),
        ],
    )
    def test_parse_rating(self, value, expected):
        assert parse_rating(value) == expected


class TestParseCost:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("500-800", 650),
            ("1,200", 1200),
            ("₹800", 800),
            ("300", 300),
            ("-", None),
            (None, None),
            ("80", 80),
        ],
    )
    def test_parse_cost(self, value, expected):
        assert parse_cost(value) == expected


class TestParseCuisines:
    def test_comma_separated(self):
        assert parse_cuisines("North Indian, Chinese") == ["North Indian", "Chinese"]

    def test_empty_defaults_unknown(self):
        assert parse_cuisines("") == ["Unknown"]
        assert parse_cuisines(None) == ["Unknown"]


class TestNormalizeCity:
    def test_bangalore_variants(self):
        assert normalize_city_from_address("942, Banashankari, Bangalore") == "Bangalore"
        assert normalize_city_from_address("Some place, Bengaluru") == "Bangalore"
        assert normalize_city_from_address("Road, Banglore") == "Bangalore"

    def test_other_cities(self):
        assert normalize_city_from_address("Connaught Place, New Delhi") == "Delhi"
        assert normalize_city_from_address("Bandra, Mumbai") == "Mumbai"


class TestMapRawRow:
    def test_sample_row(self):
        row = {
            "name": "Jalsa",
            "address": "942, 21st Main Road, 2nd Stage, Banashankari, Bangalore",
            "location": "Banashankari",
            "online_order": "Yes",
            "book_table": "Yes",
            "rate": "4.1/5",
            "votes": 775,
            "rest_type": "Casual Dining",
            "dish_liked": "Pasta, Lunch Buffet",
            "cuisines": "North Indian, Mughlai, Chinese",
            "approx_cost(for two people)": "800",
        }
        result = map_raw_row(row)
        assert result is not None
        assert result.name == "Jalsa"
        assert result.city == "Bangalore"
        assert result.area == "Banashankari"
        assert result.rating == 4.1
        assert result.cost_for_two == 800
        assert result.online_order is True
        assert "North Indian" in result.cuisines

    def test_missing_name_skipped(self):
        assert map_raw_row({"name": "", "address": "Bangalore"}) is None


class TestDeduplication:
    def test_removes_duplicates(self):
        row = {
            "name": "Jalsa",
            "address": "942, Banashankari, Bangalore",
            "location": "Banashankari",
            "online_order": "Yes",
            "book_table": "Yes",
            "rate": "4.1/5",
            "votes": 775,
            "rest_type": "Casual Dining",
            "cuisines": "North Indian",
            "approx_cost(for two people)": "800",
        }
        restaurants = [map_raw_row(row), map_raw_row(row)]
        unique, dup_count = deduplicate_restaurants([r for r in restaurants if r])
        assert len(unique) == 1
        assert dup_count == 1


class TestPriceRange:
    def test_global_classification(self):
        assert classify_price_range_global(300) == "low"
        assert classify_price_range_global(600) == "medium"
        assert classify_price_range_global(1200) == "high"
        assert classify_price_range_global(None) == "medium"

    def test_assign_price_ranges(self):
        from src.phase1.preprocessor import CleanedRestaurant

        restaurants = [
            CleanedRestaurant(
                name="A", city="Bangalore", area=None, address=None,
                cuisines=["Indian"], cost_for_two=cost, price_range="medium",
                rating=4.0, votes=10, restaurant_type=None,
                online_order=False, book_table=False, popular_dishes=[],
            )
            for cost in [200, 400, 600, 800, 1000, 1500]
        ]
        assign_price_ranges(restaurants)
        tiers = {r.cost_for_two: r.price_range for r in restaurants}
        assert tiers[200] == "low"
        assert tiers[1500] == "high"


class TestToDbDict:
    def test_serializes_lists(self):
        row = map_raw_row({
            "name": "Test",
            "address": "Bangalore",
            "cuisines": "Italian, Pizza",
            "approx_cost(for two people)": "500",
            "rate": "4.0/5",
            "votes": 10,
            "online_order": "No",
            "book_table": "No",
        })
        assert row is not None
        db_dict = to_db_dict(row)
        assert '"Italian"' in db_dict["cuisines"]
        assert db_dict["name"] == "Test"
