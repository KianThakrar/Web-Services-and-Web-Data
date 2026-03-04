"""TDD tests for Favourite CRUD endpoints (auth-protected)."""

from app.models.driver import Driver


def make_driver(db, ref="hamilton", name="Lewis Hamilton"):
    d = Driver(driver_ref=ref, name=name, first_name="Lewis", last_name="Hamilton", nationality="British")
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def register_and_login(client, username="fav_user", email="fav@test.com"):
    client.post("/api/v1/auth/register", json={"username": username, "email": email, "password": "pass123"})
    resp = client.post("/api/v1/auth/login", data={"username": username, "password": "pass123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestFavouriteCRUD:
    def test_add_favourite_returns_201(self, client, db):
        driver = make_driver(db)
        headers = register_and_login(client)
        response = client.post("/api/v1/favourites", json={"driver_id": driver.id}, headers=headers)
        assert response.status_code == 201
        assert response.json()["driver_id"] == driver.id

    def test_list_favourites_returns_own(self, client, db):
        driver = make_driver(db)
        headers = register_and_login(client)
        client.post("/api/v1/favourites", json={"driver_id": driver.id}, headers=headers)
        response = client.get("/api/v1/favourites", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_add_duplicate_favourite_returns_400(self, client, db):
        driver = make_driver(db)
        headers = register_and_login(client)
        client.post("/api/v1/favourites", json={"driver_id": driver.id}, headers=headers)
        response = client.post("/api/v1/favourites", json={"driver_id": driver.id}, headers=headers)
        assert response.status_code == 400

    def test_remove_favourite_returns_204(self, client, db):
        driver = make_driver(db)
        headers = register_and_login(client)
        create = client.post("/api/v1/favourites", json={"driver_id": driver.id}, headers=headers)
        fav_id = create.json()["id"]
        response = client.delete(f"/api/v1/favourites/{fav_id}", headers=headers)
        assert response.status_code == 204

    def test_add_favourite_requires_auth(self, client, db):
        response = client.post("/api/v1/favourites", json={"driver_id": 1})
        assert response.status_code == 401
