"""TDD tests for race read endpoints."""

from datetime import date

from app.models.race import Race


def make_race(db, season=2024, round_num=1, name="Bahrain Grand Prix"):
    r = Race(
        season=season,
        round=round_num,
        name=name,
        circuit_name="Bahrain International Circuit",
        circuit_country="Bahrain",
        date=date(2024, 3, 2),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


class TestRaceEndpoints:
    def test_list_races_returns_200(self, client, db):
        make_race(db)
        response = client.get("/api/v1/races")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_races_filter_by_season(self, client, db):
        make_race(db, season=2024, round_num=1)
        make_race(db, season=2023, round_num=1, name="Bahrain GP 2023")
        response = client.get("/api/v1/races?season=2024")
        assert response.status_code == 200
        assert all(r["season"] == 2024 for r in response.json())

    def test_list_races_supports_limit_offset(self, client, db):
        make_race(db, season=2024, round_num=1, name="Race 1")
        make_race(db, season=2024, round_num=2, name="Race 2")
        make_race(db, season=2024, round_num=3, name="Race 3")
        first_page = client.get("/api/v1/races?limit=2&offset=0")
        second_page = client.get("/api/v1/races?limit=2&offset=2")
        assert first_page.status_code == 200
        assert second_page.status_code == 200
        assert len(first_page.json()) == 2
        assert len(second_page.json()) == 1

    def test_get_race_by_id_returns_200(self, client, db):
        race = make_race(db)
        response = client.get(f"/api/v1/races/{race.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Bahrain Grand Prix"

    def test_get_race_not_found_returns_404(self, client, db):
        response = client.get("/api/v1/races/99999")
        assert response.status_code == 404
