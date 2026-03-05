"""TDD tests for analytics endpoints."""

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult


def seed_analytics_data(db):
    """Seed minimal data for analytics tests."""
    d1 = Driver(driver_ref="hamilton", name="Lewis Hamilton", first_name="Lewis", last_name="Hamilton", nationality="British")
    d2 = Driver(driver_ref="verstappen", name="Max Verstappen", first_name="Max", last_name="Verstappen", nationality="Dutch")
    c1 = Constructor(constructor_ref="mercedes", name="Mercedes", nationality="German")
    c2 = Constructor(constructor_ref="redbull", name="Red Bull", nationality="Austrian")
    r1 = Race(season=2024, round=1, name="Bahrain GP", circuit_name="Bahrain", circuit_country="Bahrain")
    r2 = Race(season=2024, round=2, name="Saudi GP", circuit_name="Jeddah", circuit_country="Saudi Arabia")
    db.add_all([d1, d2, c1, c2, r1, r2])
    db.flush()

    db.add_all([
        RaceResult(race_id=r1.id, driver_id=d1.id, constructor_id=c1.id, finish_position=1, points=25.0),
        RaceResult(race_id=r2.id, driver_id=d2.id, constructor_id=c2.id, finish_position=1, points=25.0),
        RaceResult(race_id=r1.id, driver_id=d2.id, constructor_id=c2.id, finish_position=2, points=18.0),
        RaceResult(race_id=r2.id, driver_id=d1.id, constructor_id=c1.id, finish_position=2, points=18.0),
    ])
    db.commit()
    return d1, d2, c1, c2


class TestAnalyticsEndpoints:
    def test_constructor_standings_returns_200(self, client, db):
        seed_analytics_data(db)
        response = client.get("/api/v1/analytics/constructors/standings?season=2024")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert "constructor_name" in data[0]
        assert "total_points" in data[0]

    def test_driver_standings_returns_200(self, client, db):
        seed_analytics_data(db)
        response = client.get("/api/v1/analytics/drivers/standings?season=2024")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert "driver_name" in data[0]
        assert "total_points" in data[0]

    def test_nationality_breakdown_returns_200(self, client, db):
        seed_analytics_data(db)
        response = client.get("/api/v1/analytics/drivers/nationalities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(item["nationality"] == "British" for item in data)

    def test_top_winners_returns_200(self, client, db):
        seed_analytics_data(db)
        response = client.get("/api/v1/analytics/drivers/top-winners")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "driver_name" in data[0]
        assert "wins" in data[0]

    def test_season_summary_returns_200(self, client, db):
        seed_analytics_data(db)
        response = client.get("/api/v1/analytics/seasons/2024/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["season"] == 2024
        assert data["total_races"] == 2
        assert "drivers_competed" in data

    def test_win_probability_returns_200_with_circuit(self, client, db):
        d1, d2, _, _ = seed_analytics_data(db)
        response = client.get(f"/api/v1/analytics/drivers/{d1.id}/win-probability?circuit_name=Bahrain")
        assert response.status_code == 200
        data = response.json()
        assert "win_probability" in data
        assert "factors" in data
        assert 0.0 <= data["win_probability"] <= 1.0

    def test_win_probability_returns_200_overall(self, client, db):
        d1, _, _, _ = seed_analytics_data(db)
        response = client.get(f"/api/v1/analytics/drivers/{d1.id}/win-probability")
        assert response.status_code == 200
        data = response.json()
        assert "win_probability" in data
        assert data["win_probability"] > 0

    def test_win_probability_returns_404_for_unknown_driver(self, client):
        response = client.get("/api/v1/analytics/drivers/99999/win-probability")
        assert response.status_code == 404
