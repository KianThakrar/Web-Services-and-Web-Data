"""TokenBlacklist model — stores revoked JWT IDs to enable per-token logout."""

from datetime import UTC, datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Integer, String

from app.database import Base


class TokenBlacklist(Base):
    """Revoked JWT tokens identified by their unique JTI claim."""

    __tablename__ = "token_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
