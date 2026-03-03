"""Constructor model representing Formula 1 teams."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Constructor(Base):
    """F1 constructor (team) with identification and nationality."""

    __tablename__ = "constructors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    constructor_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    nationality: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)

    race_results = relationship("RaceResult", back_populates="constructor")
