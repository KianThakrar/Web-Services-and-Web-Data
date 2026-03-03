"""RaceResult model linking drivers, constructors, and races with finishing data."""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RaceResult(Base):
    """Individual driver result for a specific race."""

    __tablename__ = "race_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    race_id: Mapped[int] = mapped_column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    constructor_id: Mapped[int] = mapped_column(Integer, ForeignKey("constructors.id"), nullable=False, index=True)
    grid_position: Mapped[int] = mapped_column(Integer, nullable=True)
    finish_position: Mapped[int] = mapped_column(Integer, nullable=True)
    position_text: Mapped[str] = mapped_column(String(10), nullable=True)
    points: Mapped[float] = mapped_column(Float, default=0.0)
    laps: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=True)
    fastest_lap_time: Mapped[str] = mapped_column(String(20), nullable=True)

    race = relationship("Race", back_populates="results")
    driver = relationship("Driver", back_populates="race_results")
    constructor = relationship("Constructor", back_populates="race_results")
