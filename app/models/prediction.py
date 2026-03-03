"""Prediction model for user race outcome predictions (CRUD resource)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prediction(Base):
    """User prediction for a race outcome — full CRUD resource."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    race_id: Mapped[int] = mapped_column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    predicted_driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("drivers.id"), nullable=False)
    predicted_position: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    race = relationship("Race", back_populates="predictions")
    predicted_driver = relationship("Driver")
