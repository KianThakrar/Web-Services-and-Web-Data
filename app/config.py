"""Application configuration loaded from environment variables."""

import secrets

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    database_url: str = "sqlite:///./app.db"
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    anthropic_api_key: str = ""
    app_name: str = "F1 Racing Intelligence API"
    debug: bool = False
    # Comma-separated allowed CORS origins; defaults to localhost dev origins only
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
    # Optional previous secret key — set during zero-downtime JWT key rotation
    secret_key_previous: str = ""
    # Optional API key for MCP SSE transport. If empty, only localhost binding is allowed.
    mcp_api_key: str = ""
    mcp_sse_host: str = "127.0.0.1"
    mcp_sse_port: int = 3001

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value):
        """Accept common environment aliases for debug/release modes."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "t", "yes", "y", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "f", "no", "n", "off", "release", "prod", "production"}:
                return False
        raise ValueError("DEBUG must be a boolean-like value")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
