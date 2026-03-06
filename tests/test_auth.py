"""TDD tests for user registration, login, and JWT-protected routes."""

import pytest


class TestRegistration:
    def test_register_returns_201_with_user_data(self, client):
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_username_returns_409(self, client):
        payload = {"username": "duplicate", "email": "a@example.com", "password": "password123"}
        client.post("/api/v1/auth/register", json=payload)
        response = client.post("/api/v1/auth/register", json={
            "username": "duplicate", "email": "b@example.com", "password": "password123"
        })
        assert response.status_code == 409

    def test_register_duplicate_email_returns_409(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "user1", "email": "same@example.com", "password": "password123"
        })
        response = client.post("/api/v1/auth/register", json={
            "username": "user2", "email": "same@example.com", "password": "password123"
        })
        assert response.status_code == 409


class TestLogin:
    def test_login_returns_access_token(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "loginuser", "email": "login@example.com", "password": "mypassword"
        })
        response = client.post("/api/v1/auth/login", data={
            "username": "loginuser", "password": "mypassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "user2", "email": "user2@example.com", "password": "correctpass"
        })
        response = client.post("/api/v1/auth/login", data={
            "username": "user2", "password": "wrongpass"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        response = client.post("/api/v1/auth/login", data={
            "username": "ghost", "password": "whatever"
        })
        assert response.status_code == 401


class TestProtectedRoutes:
    def test_get_me_without_token_returns_401(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_with_valid_token_returns_user(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "meuser", "email": "me@example.com", "password": "password123"
        })
        login = client.post("/api/v1/auth/login", data={
            "username": "meuser", "password": "password123"
        })
        token = login.json()["access_token"]
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["username"] == "meuser"


class TestLogout:
    def _register_and_login(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "logoutuser", "email": "logout@example.com", "password": "password123"
        })
        login = client.post("/api/v1/auth/login", data={
            "username": "logoutuser", "password": "password123"
        })
        return login.json()["access_token"]

    def test_logout_without_token_returns_401(self, client):
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    def test_logout_with_valid_token_returns_200(self, client):
        token = self._register_and_login(client)
        response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    def test_logout_blacklists_token_so_me_returns_401(self, client):
        token = self._register_and_login(client)
        client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
