import pytest
from pydantic import ValidationError

from src.phase2.api.normalizer import (
    CityNotFoundError,
    normalize_area,
    normalize_location,
    normalize_min_rating,
    normalize_request,
    sanitize_additional_preferences,
)
from src.phase2.api.schemas import RecommendationRequest


class TestNormalizeLocation:
    def test_bengaluru_alias(self):
        assert normalize_location("Bengaluru") == "Bangalore"

    def test_case_insensitive(self):
        assert normalize_location("bengaluru") == "Bangalore"

    def test_unknown_passthrough(self):
        assert normalize_location("Jaipur") == "Jaipur"


class TestNormalizeArea:
    def test_all_bangalore_returns_none(self):
        assert normalize_area("All Bangalore") is None

    def test_hsr_layout_alias(self):
        assert normalize_area("HSR Layout") == "HSR"

    def test_none(self):
        assert normalize_area(None) is None


class TestNormalizeMinRating:
    def test_rounds_to_one_decimal(self):
        assert normalize_min_rating(4.05) == 4.0
        assert normalize_min_rating(3.96) == 4.0


class TestSanitizeAdditionalPreferences:
    def test_strips_whitespace(self):
        assert sanitize_additional_preferences("  family friendly  ") == "family friendly"

    def test_rejects_html(self):
        with pytest.raises(ValueError, match="HTML"):
            sanitize_additional_preferences("<script>alert(1)</script>")

    def test_none_and_empty(self):
        assert sanitize_additional_preferences(None) is None
        assert sanitize_additional_preferences("   ") is None


class TestNormalizeRequest:
    def test_full_normalization(self):
        prefs = normalize_request(
            location=" Bengaluru ",
            max_budget=800,
            cuisine=" Italian ",
            min_rating=4.05,
            additional_preferences="family friendly",
            area="HSR Layout",
        )
        assert prefs.location == "Bangalore"
        assert prefs.area == "HSR"
        assert prefs.cuisine == "Italian"
        assert prefs.min_rating == 4.0
        assert prefs.max_budget == 800


class TestRecommendationRequestValidation:
    def test_valid_request(self):
        req = RecommendationRequest(
            location="Bangalore",
            max_budget=800,
            cuisine="Italian",
            min_rating=4.0,
            area="HSR",
        )
        assert req.location == "Bangalore"
        assert req.max_budget == 800

    def test_invalid_max_budget(self):
        with pytest.raises(ValidationError):
            RecommendationRequest(
                location="Bangalore",
                max_budget=50,
                cuisine="Italian",
                min_rating=4.0,
            )

    def test_min_rating_out_of_range(self):
        with pytest.raises(ValidationError):
            RecommendationRequest(
                location="Bangalore",
                max_budget=800,
                cuisine="Italian",
                min_rating=6.0,
            )

    def test_rejects_script_in_additional_preferences(self):
        with pytest.raises(ValidationError):
            RecommendationRequest(
                location="Bangalore",
                max_budget=800,
                cuisine="Italian",
                min_rating=4.0,
                additional_preferences="<script>bad</script>",
            )


class TestCityNotFoundError:
    def test_message(self):
        err = CityNotFoundError("Jaipur")
        assert "Jaipur" in str(err)
        assert "/api/v1/meta/cities" in str(err)
