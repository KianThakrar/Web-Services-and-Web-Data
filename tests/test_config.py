"""Tests for environment configuration parsing."""

import pytest

from app.config import Settings


def test_debug_accepts_release_alias() -> None:
    settings = Settings(debug="release")
    assert settings.debug is False


def test_debug_accepts_development_alias() -> None:
    settings = Settings(debug="development")
    assert settings.debug is True


def test_debug_rejects_unknown_string() -> None:
    with pytest.raises(ValueError):
        Settings(debug="sometimes")
