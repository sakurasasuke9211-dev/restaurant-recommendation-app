class TestGetAreas:
    def test_includes_all_bangalore_first(self, client):
        response = client.get("/api/v1/meta/areas", params={"city": "Bangalore"})
        assert response.status_code == 200
        areas = response.json()["areas"]
        assert areas[0] == "All Bangalore"
        assert "Indiranagar" in areas

    def test_requires_city(self, client):
        response = client.get("/api/v1/meta/areas")
        assert response.status_code == 422
