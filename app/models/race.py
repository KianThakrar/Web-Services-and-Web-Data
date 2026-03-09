"""Race model representing individual Formula 1 grand prix events."""

from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Race(Base):
    """F1 grand prix with circuit, season, and scheduling data."""

    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("season", "round", name="uq_races_season_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    circuit_name: Mapped[str] = mapped_column(String(300), nullable=False)
    circuit_location: Mapped[str] = mapped_column(String(200), nullable=True)
    circuit_country: Mapped[str] = mapped_column(String(100), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)

    results = relationship("RaceResult", back_populates="race")
    predictions = relationship("Prediction", back_populates="race")
