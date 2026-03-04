"""TDD tests for driver read endpoints."""

from app.models.driver import Driver


def make_driver(db, ref="hamilton", name="Lewis Hamilton", nationality="British"):
    d = Driver(driver_ref=ref, name=name, first_name="Lewis", last_name="Hamilton", nationality=nationality)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


class TestDriverEndpoints:
    def test_list_drivers_returns_200(self, client, db):
        make_driver(db)
        response = client.get("/api/v1/drivers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_list_drivers_filter_by_nationality(self, client, db):
        make_driver(db, ref="hamilton", nationality="British")
        make_driver(db, ref="alonso", name="Fernando Alonso", nationality="Spanish")
        response = client.get("/api/v1/drivers?nationality=British")
        assert response.status_code == 200
        assert all(d["nationality"] == "British" for d in response.json())

    def test_get_driver_by_id_returns_200(self, client, db):
        driver = make_driver(db)
        response = client.get(f"/api/v1/drivers/{driver.id}")
        assert response.status_code == 200
        assert response.json()["driver_ref"] == "hamilton"

    def test_get_driver_not_found_returns_404(self, client, db):
        response = client.get("/api/v1/drivers/99999")
        assert response.status_code == 404
