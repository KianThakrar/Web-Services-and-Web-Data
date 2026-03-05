"""SQLAlchemy model registry — all models must be imported here for Alembic discovery."""

from app.models.user import User
from app.models.driver import Driver
from app.models.constructor import Constructor
from app.models.race import Race
from app.models.race_result import RaceResult
from app.models.prediction import Prediction
from app.models.favourite import Favourite
from app.models.ai_summary import AISummaryCache
from app.models.token_blacklist import TokenBlacklist

__all__ = [
    "User",
    "Driver",
    "Constructor",
    "Race",
    "RaceResult",
    "Prediction",
    "Favourite",
    "AISummaryCache",
    "TokenBlacklist",
]
