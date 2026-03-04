"""TDD tests for Prediction full CRUD endpoints (auth-protected)."""

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race


def seed_fixtures(db):
    driver = Driver(driver_ref="hamilton", name="Lewis Hamilton", first_name="Lewis", last_name="Hamilton", nationality="British")
    constructor = Constructor(constructor_ref="mercedes", name="Mercedes", nationality="German")
    race = Race(season=2024, round=1, name="Bahrain GP", circuit_name="Bahrain", circuit_country="Bahrain")
    db.add_all([driver, constructor, race])
    db.commit()
    db.refresh(driver); db.refresh(race)
    return driver, race


def register_and_login(client):
    client.post("/api/v1/auth/register", json={"username": "pred_user", "email": "p@test.com", "password": "password123"})
    resp = client.post("/api/v1/auth/login", data={"username": "pred_user", "password": "password123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestPredictionCRUD:
    def test_create_prediction_returns_201(self, client, db):
        driver, race = seed_fixtures(db)
        headers = register_and_login(client)
        response = client.post("/api/v1/predictions", json={
            "race_id": race.id,
            "predicted_driver_id": driver.id,
            "predicted_position": 1,
            "notes": "Hamilton to dominate"
        }, headers=headers)
        assert response.status_code == 201
        assert response.json()["predicted_position"] == 1

    def test_list_predictions_returns_own_only(self, client, db):
        driver, race = seed_fixtures(db)
        headers = register_and_login(client)
        client.post("/api/v1/predictions", json={
            "race_id": race.id, "predicted_driver_id": driver.id, "predicted_position": 1
        }, headers=headers)
        response = client.get("/api/v1/predictions", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_update_prediction_returns_200(self, client, db):
        driver, race = seed_fixtures(db)
        headers = register_and_login(client)
        create = client.post("/api/v1/predictions", json={
            "race_id": race.id, "predicted_driver_id": driver.id, "predicted_position": 1
        }, headers=headers)
        pred_id = create.json()["id"]
        response = client.put(f"/api/v1/predictions/{pred_id}", json={
            "race_id": race.id, "predicted_driver_id": driver.id, "predicted_position": 3, "notes": "Updated"
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["predicted_position"] == 3

    def test_delete_prediction_returns_204(self, client, db):
        driver, race = seed_fixtures(db)
        headers = register_and_login(client)
        create = client.post("/api/v1/predictions", json={
            "race_id": race.id, "predicted_driver_id": driver.id, "predicted_position": 1
        }, headers=headers)
        pred_id = create.json()["id"]
        response = client.delete(f"/api/v1/predictions/{pred_id}", headers=headers)
        assert response.status_code == 204

    def test_create_prediction_requires_auth(self, client, db):
        response = client.post("/api/v1/predictions", json={
            "race_id": 1, "predicted_driver_id": 1, "predicted_position": 1
        })
        assert response.status_code == 401
