"""Driver model representing Formula 1 drivers."""

from sqlalchemy import Integer, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Driver(Base):
    """F1 driver with career statistics and biographical data."""

    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    driver_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(20), nullable=True)
    nationality: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=True)
    code: Mapped[str] = mapped_column(String(10), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)

    race_results = relationship("RaceResult", back_populates="driver")
    favourited_by = relationship("Favourite", back_populates="driver")
