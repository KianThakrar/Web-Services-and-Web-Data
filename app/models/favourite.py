"""Favourite model for user-driver bookmarking (CRUD resource)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Favourite(Base):
    """User favourite driver bookmark — CRUD resource with uniqueness constraint."""

    __tablename__ = "favourites"
    __table_args__ = (
        UniqueConstraint("user_id", "driver_id", name="uq_user_driver_favourite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favourites")
    driver = relationship("Driver", back_populates="favourited_by")
