"""TDD tests for advanced analytics endpoints — head-to-head, circuit performance, era dominance."""

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult


def seed_h2h_data(db):
    """Two drivers competing across multiple races for head-to-head tests."""
    d1 = Driver(driver_ref="hamilton", name="Lewis Hamilton", first_name="Lewis", last_name="Hamilton", nationality="British")
    d2 = Driver(driver_ref="verstappen", name="Max Verstappen", first_name="Max", last_name="Verstappen", nationality="Dutch")
    c1 = Constructor(constructor_ref="mercedes", name="Mercedes", nationality="German")
    c2 = Constructor(constructor_ref="redbull", name="Red Bull", nationality="Austrian")

    r1 = Race(season=2021, round=1, name="Bahrain GP", circuit_name="Bahrain International Circuit", circuit_country="Bahrain")
    r2 = Race(season=2021, round=2, name="Emilia Romagna GP", circuit_name="Autodromo Enzo e Dino Ferrari", circuit_country="Italy")
    r3 = Race(season=2022, round=1, name="Bahrain GP", circuit_name="Bahrain International Circuit", circuit_country="Bahrain")
    db.add_all([d1, d2, c1, c2, r1, r2, r3])
    db.flush()

    db.add_all([
        # Race 1: Hamilton wins
        RaceResult(race_id=r1.id, driver_id=d1.id, constructor_id=c1.id, finish_position=1, points=25.0, grid_position=2),
        RaceResult(race_id=r1.id, driver_id=d2.id, constructor_id=c2.id, finish_position=2, points=18.0, grid_position=1),
        # Race 2: Verstappen wins
        RaceResult(race_id=r2.id, driver_id=d2.id, constructor_id=c2.id, finish_position=1, points=25.0, grid_position=1),
        RaceResult(race_id=r2.id, driver_id=d1.id, constructor_id=c1.id, finish_position=2, points=18.0, grid_position=2),
        # Race 3: Verstappen wins, Hamilton DNF
        RaceResult(race_id=r3.id, driver_id=d2.id, constructor_id=c2.id, finish_position=1, points=25.0, grid_position=1),
        RaceResult(race_id=r3.id, driver_id=d1.id, constructor_id=c1.id, finish_position=None, points=0.0, grid_position=3, position_text="DNF"),
    ])
    db.commit()
    db.refresh(d1); db.refresh(d2)
    return d1, d2, r1


def seed_circuit_data(db):
    """Single driver with results at the same circuit across multiple seasons."""
    d = Driver(driver_ref="hamilton", name="Lewis Hamilton", first_name="Lewis", last_name="Hamilton", nationality="British")
    c = Constructor(constructor_ref="mercedes", name="Mercedes", nationality="German")
    r1 = Race(season=2020, round=5, name="British GP", circuit_name="Silverstone Circuit", circuit_country="United Kingdom")
    r2 = Race(season=2021, round=10, name="British GP", circuit_name="Silverstone Circuit", circuit_country="United Kingdom")
    r3 = Race(season=2022, round=10, name="British GP", circuit_name="Silverstone Circuit", circuit_country="United Kingdom")
    db.add_all([d, c, r1, r2, r3])
    db.flush()
    db.add_all([
        RaceResult(race_id=r1.id, driver_id=d.id, constructor_id=c.id, finish_position=1, points=25.0),
        RaceResult(race_id=r2.id, driver_id=d.id, constructor_id=c.id, finish_position=1, points=25.0),
        RaceResult(race_id=r3.id, driver_id=d.id, constructor_id=c.id, finish_position=3, points=15.0),
    ])
    db.commit()
    db.refresh(d)
    return d


def seed_era_data(db):
    """Multiple constructors across different decades."""
    c1 = Constructor(constructor_ref="ferrari", name="Ferrari", nationality="Italian")
    c2 = Constructor(constructor_ref="mercedes", name="Mercedes", nationality="German")
    c3 = Constructor(constructor_ref="redbull", name="Red Bull", nationality="Austrian")
    r2010 = Race(season=2010, round=1, name="Bahrain GP", circuit_name="Bahrain", circuit_country="Bahrain")
    r2011 = Race(season=2011, round=1, name="Bahrain GP", circuit_name="Bahrain", circuit_country="Bahrain")
    r2020 = Race(season=2020, round=1, name="Austrian GP", circuit_name="Red Bull Ring", circuit_country="Austria")
    r2021 = Race(season=2021, round=1, name="Bahrain GP", circuit_name="Bahrain", circuit_country="Bahrain")
    d = Driver(driver_ref="test_driver", name="Test Driver", first_name="Test", last_name="Driver", nationality="British")
    db.add_all([c1, c2, c3, r2010, r2011, r2020, r2021, d])
    db.flush()
    db.add_all([
        RaceResult(race_id=r2010.id, driver_id=d.id, constructor_id=c1.id, finish_position=1, points=25.0),
        RaceResult(race_id=r2011.id, driver_id=d.id, constructor_id=c1.id, finish_position=1, points=25.0),
        RaceResult(race_id=r2020.id, driver_id=d.id, constructor_id=c2.id, finish_position=1, points=25.0),
        RaceResult(race_id=r2021.id, driver_id=d.id, constructor_id=c3.id, finish_position=1, points=25.0),
    ])
    db.commit()
    return c1, c2, c3


class TestHeadToHead:
    def test_h2h_returns_200(self, client, db):
        d1, d2, _ = seed_h2h_data(db)
        response = client.get(f"/api/v1/analytics/drivers/{d1.id}/vs/{d2.id}")
        assert response.status_code == 200

    def test_h2h_contains_both_drivers(self, client, db):
        d1, d2, _ = seed_h2h_data(db)
        data = client.get(f"/api/v1/analytics/drivers/{d1.id}/vs/{d2.id}").json()
        assert data["driver_1"]["driver_name"] == "Lewis Hamilton"
        assert data["driver_2"]["driver_name"] == "Max Verstappen"

    def test_h2h_head_to_head_wins_correct(self, client, db):
        d1, d2, _ = seed_h2h_data(db)
        data = client.get(f"/api/v1/analytics/drivers/{d1.id}/vs/{d2.id}").json()
        # Hamilton finished ahead in race 1, Verstappen in races 2 and 3
        assert data["head_to_head"]["driver_1_ahead"] == 1
        assert data["head_to_head"]["driver_2_ahead"] == 2

    def test_h2h_total_wins_correct(self, client, db):
        d1, d2, _ = seed_h2h_data(db)
        data = client.get(f"/api/v1/analytics/drivers/{d1.id}/vs/{d2.id}").json()
        assert data["driver_1"]["total_wins"] == 1
        assert data["driver_2"]["total_wins"] == 2

    def test_h2h_driver_not_found_returns_404(self, client, db):
        response = client.get("/api/v1/analytics/drivers/99999/vs/99998")
        assert response.status_code == 404


class TestCircuitPerformance:
    def test_circuit_performance_returns_200(self, client, db):
        driver = seed_circuit_data(db)
        response = client.get(f"/api/v1/analytics/drivers/{driver.id}/circuits/Silverstone Circuit")
        assert response.status_code == 200

    def test_circuit_performance_has_correct_stats(self, client, db):
        driver = seed_circuit_data(db)
        data = client.get(f"/api/v1/analytics/drivers/{driver.id}/circuits/Silverstone Circuit").json()
        assert data["driver_name"] == "Lewis Hamilton"
        assert data["circuit_name"] == "Silverstone Circuit"
        assert data["appearances"] == 3
        assert data["wins"] == 2
        assert data["best_finish"] == 1
        assert round(data["average_finish"], 2) == round((1 + 1 + 3) / 3, 2)

    def test_circuit_no_results_returns_404(self, client, db):
        driver = seed_circuit_data(db)
        response = client.get(f"/api/v1/analytics/drivers/{driver.id}/circuits/Monaco Circuit")
        assert response.status_code == 404


class TestEraDominance:
    def test_era_dominance_returns_200(self, client, db):
        seed_era_data(db)
        response = client.get("/api/v1/analytics/constructors/era-dominance")
        assert response.status_code == 200

    def test_era_dominance_returns_list_of_eras(self, client, db):
        seed_era_data(db)
        data = client.get("/api/v1/analytics/constructors/era-dominance").json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "era" in data[0]
        assert "dominant_constructor" in data[0]
        assert "total_points" in data[0]

    def test_era_dominance_correct_winner(self, client, db):
        seed_era_data(db)
        data = client.get("/api/v1/analytics/constructors/era-dominance").json()
        era_2010s = next((e for e in data if e["era"] == "2010s"), None)
        assert era_2010s is not None
        assert era_2010s["dominant_constructor"] == "Ferrari"
