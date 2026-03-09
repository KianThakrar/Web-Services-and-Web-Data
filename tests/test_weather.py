"""TDD tests for weather analytics endpoints."""

from datetime import date

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult
from app.models.weather_cache import WeatherCache


def seed_weather_data(db):
    """Seed minimal data for weather analytics tests."""
    d1 = Driver(driver_ref="hamilton", name="Lewis Hamilton", first_name="Lewis", last_name="Hamilton", nationality="British")
    d2 = Driver(driver_ref="verstappen", name="Max Verstappen", first_name="Max", last_name="Verstappen", nationality="Dutch")
    c1 = Constructor(constructor_ref="mercedes", name="Mercedes", nationality="German")

    # Two races at same circuit — one wet, one dry
    r1 = Race(season=2020, round=1, name="British GP", circuit_name="Silverstone Circuit", circuit_location="Silverstone", circuit_country="UK", date=date(2020, 8, 2))
    r2 = Race(season=2021, round=10, name="British GP", circuit_name="Silverstone Circuit", circuit_location="Silverstone", circuit_country="UK", date=date(2021, 7, 18))
    # One race at a different circuit (dry)
    r3 = Race(season=2021, round=1, name="Bahrain GP", circuit_name="Bahrain International Circuit", circuit_location="Sakhir", circuit_country="Bahrain", date=date(2021, 3, 28))

    db.add_all([d1, d2, c1, r1, r2, r3])
    db.flush()

    # Race results
    db.add_all([
        RaceResult(race_id=r1.id, driver_id=d1.id, constructor_id=c1.id, finish_position=1, points=25.0),
        RaceResult(race_id=r1.id, driver_id=d2.id, constructor_id=c1.id, finish_position=2, points=18.0),
        RaceResult(race_id=r2.id, driver_id=d2.id, constructor_id=c1.id, finish_position=1, points=25.0),
        RaceResult(race_id=r2.id, driver_id=d1.id, constructor_id=c1.id, finish_position=3, points=15.0),
        RaceResult(race_id=r3.id, driver_id=d1.id, constructor_id=c1.id, finish_position=2, points=18.0),
        RaceResult(race_id=r3.id, driver_id=d2.id, constructor_id=c1.id, finish_position=1, points=25.0),
    ])

    # Weather — r1 is wet (rain, code 63), r2 is dry (clear, code 0), r3 is dry
    db.add_all([
        WeatherCache(race_id=r1.id, temperature_max=18.5, temperature_min=12.3, precipitation_mm=8.2, wind_speed_max=32.0, weather_code=63),
        WeatherCache(race_id=r2.id, temperature_max=24.1, temperature_min=15.0, precipitation_mm=0.0, wind_speed_max=18.5, weather_code=0),
        WeatherCache(race_id=r3.id, temperature_max=29.0, temperature_min=20.5, precipitation_mm=0.0, wind_speed_max=22.0, weather_code=1),
    ])
    db.commit()
    return d1, d2, r1, r2, r3


class TestWeatherEndpoints:
    def test_circuit_weather_profile_returns_200(self, client, db):
        seed_weather_data(db)
        response = client.get("/api/v1/analytics/weather/circuits/Silverstone Circuit")
        assert response.status_code == 200
        data = response.json()
        assert data["circuit_name"] == "Silverstone Circuit"
        assert data["total_races_with_data"] == 2
        assert data["wet_races"] == 1
        assert data["dry_races"] == 1
        assert data["wet_race_percentage"] == 50.0
        assert data["avg_temperature_max"] is not None
        assert "race_history" in data
        assert len(data["race_history"]) == 2

    def test_driver_weather_performance_returns_200(self, client, db):
        d1, d2, *_ = seed_weather_data(db)
        response = client.get(f"/api/v1/analytics/weather/drivers/{d1.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["driver_name"] == "Lewis Hamilton"
        assert data["total_races_with_weather_data"] == 3
        assert data["wet"]["races"] == 1
        assert data["dry"]["races"] == 2
        assert data["wet"]["wins"] == 1  # Hamilton won the wet race
        assert "verdict" in data

    def test_race_weather_impact_returns_200(self, client, db):
        _, _, r1, *_ = seed_weather_data(db)
        response = client.get(f"/api/v1/analytics/weather/races/{r1.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["race_name"] == "British GP"
        assert data["weather"]["is_wet"] is True
        assert data["weather"]["precipitation_mm"] == 8.2
        assert data["weather"]["condition"] == "Moderate rain"
        assert len(data["results"]) == 2

    def test_circuit_weather_returns_404_for_unknown(self, client):
        response = client.get("/api/v1/analytics/weather/circuits/Nonexistent Circuit")
        assert response.status_code == 404

    def test_driver_weather_returns_404_for_unknown(self, client):
        response = client.get("/api/v1/analytics/weather/drivers/99999")
        assert response.status_code == 404
