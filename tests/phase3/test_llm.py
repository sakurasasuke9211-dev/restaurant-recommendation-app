import json
from unittest.mock import MagicMock, patch

import pytest

from src.phase3.llm import (
    LLMError,
    LLMResponseError,
    complete,
    is_llm_available,
    parse_llm_response,
    validate_llm_recommendations,
)


SAMPLE_LLM_JSON = json.dumps(
    {
        "summary": "Great Italian picks in Bangalore.",
        "recommendations": [
            {
                "rank": 1,
                "restaurant_id": 42,
                "restaurant_name": "Truffles",
                "explanation": "Highly rated Italian-American spot.",
            }
        ],
    }
)


class TestLLMAvailability:
    @patch("src.phase3.llm.LLM_ENABLED", True)
    @patch("src.phase3.llm._groq_api_key", return_value=None)
    def test_unavailable_without_key(self, _mock_key):
        assert is_llm_available() is False

    @patch("src.phase3.llm.LLM_ENABLED", False)
    @patch("src.phase3.llm._groq_api_key", return_value=None)
    def test_complete_raises_without_key(self, _mock_key):
        with pytest.raises(LLMError):
            complete([{"role": "user", "content": "test"}])


class TestParseLLMResponse:
    def test_parses_valid_json(self):
        data = parse_llm_response(SAMPLE_LLM_JSON)
        assert data["summary"] == "Great Italian picks in Bangalore."
        assert len(data["recommendations"]) == 1

    def test_rejects_invalid_json(self):
        with pytest.raises(LLMResponseError):
            parse_llm_response("not json")

    def test_rejects_missing_fields(self):
        with pytest.raises(LLMResponseError):
            parse_llm_response('{"summary": "only summary"}')


class TestValidateLLMRecommendations:
    def test_validates_against_candidate_set(self):
        data = parse_llm_response(SAMPLE_LLM_JSON)
        validated = validate_llm_recommendations(data, candidate_ids={42}, max_results=5)
        assert len(validated["recommendations"]) == 1

    def test_rejects_unknown_restaurant_id(self):
        data = parse_llm_response(SAMPLE_LLM_JSON)
        validated = validate_llm_recommendations(data, candidate_ids={99}, max_results=5)
        assert validated["recommendations"] == []


class TestGroqCompleteMocked:
    @patch("src.phase3.llm.Groq")
    @patch("src.phase3.llm.is_llm_available", return_value=True)
    @patch("src.phase3.llm._groq_api_key", return_value="test-key")
    def test_complete_returns_content(self, _key, _available, mock_groq_cls):
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=SAMPLE_LLM_JSON))]
        )
        result = complete([{"role": "user", "content": "test"}])
        assert "Truffles" in result
        mock_client.chat.completions.create.assert_called_once()
