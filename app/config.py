"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/f1_racing_db"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    anthropic_api_key: str = ""
    app_name: str = "F1 Racing Intelligence API"
    debug: bool = False
    # Comma-separated allowed CORS origins; defaults to localhost dev origins only
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
