class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["database"] == "connected"
        assert body["restaurant_count"] == 3
        assert isinstance(body["llm_available"], bool)
        assert "X-Request-ID" in response.headers


class TestMetaEndpoints:
    def test_list_cities(self, client):
        response = client.get("/api/v1/meta/cities")
        assert response.status_code == 200
        assert response.json()["cities"] == ["Bangalore"]

    def test_list_areas(self, client):
        response = client.get("/api/v1/meta/areas", params={"city": "Bangalore"})
        assert response.status_code == 200
        areas = response.json()["areas"]
        assert areas[0] == "All Bangalore"
        assert "Indiranagar" in areas

    def test_list_areas_unknown_city(self, client):
        response = client.get("/api/v1/meta/areas", params={"city": "Jaipur"})
        assert response.status_code == 404

    def test_list_cuisines(self, client):
        response = client.get("/api/v1/meta/cuisines")
        assert response.status_code == 200
        cuisines = response.json()["cuisines"]
        assert "Italian" in cuisines
        assert "Biryani" in cuisines

    def test_list_cuisines_by_city(self, client):
        response = client.get("/api/v1/meta/cuisines", params={"city": "Bengaluru"})
        assert response.status_code == 200
        assert "Italian" in response.json()["cuisines"]

    def test_list_cuisines_unknown_city(self, client):
        response = client.get("/api/v1/meta/cuisines", params={"city": "Jaipur"})
        assert response.status_code == 404


class TestRecommendationsEndpoint:
    def test_valid_recommendation_request(self, client):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bengaluru",
                "max_budget": 800,
                "cuisine": "Italian",
                "min_rating": 4.0,
                "additional_preferences": "family friendly",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["llm_used"] is False
        assert body["meta"]["total_candidates"] >= 1
        assert len(body["recommendations"]) >= 1
        assert body["recommendations"][0]["rank"] == 1
        assert "Italian" in body["recommendations"][0]["cuisines"]
        assert "relaxation_steps" in body["meta"]

    def test_unknown_city_returns_404(self, client):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Jaipur",
                "max_budget": 800,
                "cuisine": "Italian",
                "min_rating": 4.0,
            },
        )
        assert response.status_code == 404
        assert "Jaipur" in response.json()["detail"]

    def test_invalid_max_budget_returns_422(self, client):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bangalore",
                "max_budget": 10,
                "cuisine": "Italian",
                "min_rating": 4.0,
            },
        )
        assert response.status_code == 422

    def test_invalid_rating_returns_422(self, client):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bangalore",
                "max_budget": 800,
                "cuisine": "Italian",
                "min_rating": 10.0,
            },
        )
        assert response.status_code == 422

    def test_html_in_preferences_returns_422(self, client):
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bangalore",
                "max_budget": 800,
                "cuisine": "Italian",
                "min_rating": 4.0,
                "additional_preferences": "<script>x</script>",
            },
        )
        assert response.status_code == 422

    def test_openapi_docs_available(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_available(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "/api/v1/recommendations" in schema["paths"]
