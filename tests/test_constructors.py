"""TDD tests for constructor read endpoints."""

from app.models.constructor import Constructor


def make_constructor(db, ref="mercedes", name="Mercedes", nationality="German"):
    c = Constructor(constructor_ref=ref, name=name, nationality=nationality)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


class TestConstructorEndpoints:
    def test_list_constructors_returns_200(self, client, db):
        make_constructor(db)
        response = client.get("/api/v1/constructors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_constructors_filter_by_nationality(self, client, db):
        make_constructor(db, ref="mercedes", nationality="German")
        make_constructor(db, ref="ferrari", name="Ferrari", nationality="Italian")
        response = client.get("/api/v1/constructors?nationality=German")
        assert response.status_code == 200
        assert all(c["nationality"] == "German" for c in response.json())

    def test_list_constructors_supports_limit_offset(self, client, db):
        make_constructor(db, ref="mercedes", name="Mercedes")
        make_constructor(db, ref="ferrari", name="Ferrari")
        make_constructor(db, ref="red_bull", name="Red Bull")
        first_page = client.get("/api/v1/constructors?limit=2&offset=0")
        second_page = client.get("/api/v1/constructors?limit=2&offset=2")
        assert first_page.status_code == 200
        assert second_page.status_code == 200
        assert len(first_page.json()) == 2
        assert len(second_page.json()) == 1

    def test_get_constructor_by_id_returns_200(self, client, db):
        c = make_constructor(db)
        response = client.get(f"/api/v1/constructors/{c.id}")
        assert response.status_code == 200
        assert response.json()["constructor_ref"] == "mercedes"

    def test_get_constructor_not_found_returns_404(self, client, db):
        response = client.get("/api/v1/constructors/99999")
        assert response.status_code == 404
