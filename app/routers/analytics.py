"""Analytics endpoints — aggregated F1 statistics and insights."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import (
    get_constructor_standings,
    get_driver_nationality_breakdown,
    get_driver_standings,
    get_season_summary,
    get_top_race_winners,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/constructors/standings")
def constructor_standings(season: int, db: Session = Depends(get_db)):
    """Return constructor championship standings for a season, ranked by points."""
    return get_constructor_standings(db, season)


@router.get("/drivers/standings")
def driver_standings(season: int, db: Session = Depends(get_db)):
    """Return driver championship standings for a season, ranked by points."""
    return get_driver_standings(db, season)


@router.get("/drivers/nationalities")
def driver_nationalities(db: Session = Depends(get_db)):
    """Return a breakdown of all drivers by nationality."""
    return get_driver_nationality_breakdown(db)


@router.get("/drivers/top-winners")
def top_winners(limit: int = 10, db: Session = Depends(get_db)):
    """Return the top race winners of all time by win count."""
    return get_top_race_winners(db, limit)


@router.get("/seasons/{season}/summary")
def season_summary(season: int, db: Session = Depends(get_db)):
    """Return a high-level statistical summary for a given season."""
    return get_season_summary(db, season)
