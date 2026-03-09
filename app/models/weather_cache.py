"""WeatherCache model storing historical weather conditions for each race."""

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WeatherCache(Base):
    """Cached weather data for a specific race, fetched from Open-Meteo archive API."""

    __tablename__ = "weather_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    race_id: Mapped[int] = mapped_column(Integer, ForeignKey("races.id"), nullable=False, unique=True, index=True)
    temperature_max: Mapped[float] = mapped_column(Float, nullable=True)
    temperature_min: Mapped[float] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[float] = mapped_column(Float, nullable=True)
    wind_speed_max: Mapped[float] = mapped_column(Float, nullable=True)
    weather_code: Mapped[int] = mapped_column(Integer, nullable=True)

    race = relationship("Race")
