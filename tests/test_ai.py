"""TDD tests for the AI race summary endpoint."""

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult


def seed_race_with_results(db):
    d1 = Driver(driver_ref="hamilton", name="Lewis Hamilton", first_name="Lewis", last_name="Hamilton", nationality="British")
    d2 = Driver(driver_ref="verstappen", name="Max Verstappen", first_name="Max", last_name="Verstappen", nationality="Dutch")
    c1 = Constructor(constructor_ref="mercedes", name="Mercedes", nationality="German")
    c2 = Constructor(constructor_ref="redbull", name="Red Bull", nationality="Austrian")
    race = Race(season=2024, round=1, name="Bahrain Grand Prix", circuit_name="Bahrain International Circuit", circuit_country="Bahrain")
    db.add_all([d1, d2, c1, c2, race])
    db.flush()
    db.add_all([
        RaceResult(race_id=race.id, driver_id=d1.id, constructor_id=c1.id, finish_position=1, points=25.0, status="Finished"),
        RaceResult(race_id=race.id, driver_id=d2.id, constructor_id=c2.id, finish_position=2, points=18.0, status="Finished"),
    ])
    db.commit()
    db.refresh(race)
    return race


class TestAISummaryEndpoint:
    def test_race_summary_returns_200(self, client, db):
        race = seed_race_with_results(db)
        response = client.get(f"/api/v1/ai/races/{race.id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "race_id" in data
        assert "summary" in data
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 10

    def test_race_summary_not_found_returns_404(self, client, db):
        response = client.get("/api/v1/ai/races/99999/summary")
        assert response.status_code == 404

    def test_race_summary_contains_cached_flag(self, client, db):
        race = seed_race_with_results(db)
        response = client.get(f"/api/v1/ai/races/{race.id}/summary")
        assert response.status_code == 200
        assert "cached" in response.json()
