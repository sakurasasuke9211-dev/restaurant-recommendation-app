from unittest.mock import patch


class TestOrchestratorWithGroq:
    @patch("src.phase2.services.orchestrator._engine.run")
    def test_uses_groq_when_available(self, mock_run, client):
        from src.phase2.api.schemas import RecommendationItem, RecommendationMeta, RecommendationResponse

        mock_run.return_value = RecommendationResponse(
            summary="Groq powered summary.",
            recommendations=[
                RecommendationItem(
                    rank=1,
                    restaurant_id=1,
                    name="Truffles",
                    area="St Marks",
                    cuisines=["Italian"],
                    rating=4.6,
                    cost_for_two=700,
                    price_range="medium",
                    explanation="Excellent Italian spot.",
                )
            ],
            meta=RecommendationMeta(
                total_candidates=5,
                filters_relaxed=False,
                llm_used=True,
                processing_time_ms=100,
                relaxation_steps=[],
            ),
        )
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bangalore",
                "max_budget": 800,
                "cuisine": "Italian",
                "min_rating": 4.0,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["llm_used"] is True
        assert body["recommendations"][0]["name"] == "Truffles"

    @patch("src.phase2.services.orchestrator._engine.run")
    def test_fallback_when_llm_disabled(self, mock_run, client):
        from src.phase2.api.schemas import RecommendationMeta, RecommendationResponse

        mock_run.return_value = RecommendationResponse(
            summary="Fallback summary.",
            recommendations=[],
            meta=RecommendationMeta(
                total_candidates=0,
                filters_relaxed=False,
                llm_used=False,
                processing_time_ms=10,
                relaxation_steps=[],
            ),
        )
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bangalore",
                "max_budget": 800,
                "cuisine": "Italian",
                "min_rating": 4.0,
            },
        )
        assert response.status_code == 200
        assert response.json()["meta"]["llm_used"] is False
