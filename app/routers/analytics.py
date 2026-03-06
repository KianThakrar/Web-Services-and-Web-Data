"""Analytics endpoints — aggregated F1 statistics and insights."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import (
    get_constructor_era_dominance,
    get_constructor_standings,
    get_driver_circuit_performance,
    get_driver_nationality_breakdown,
    get_driver_standings,
    get_head_to_head,
    get_season_summary,
    get_top_race_winners,
    get_win_probability,
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
def top_winners(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    """Return the top race winners of all time by win count (max 100)."""
    return get_top_race_winners(db, limit)


@router.get("/seasons/{season}/summary")
def season_summary(season: int, db: Session = Depends(get_db)):
    """Return a high-level statistical summary for a given season."""
    return get_season_summary(db, season)


@router.get("/drivers/{driver1_id}/vs/{driver2_id}")
def head_to_head(driver1_id: int, driver2_id: int, year_from: int | None = None, year_to: int | None = None, db: Session = Depends(get_db)):
    """
    Head-to-head career comparison between two drivers.

    Returns full career stats for each driver plus direct race comparisons —
    how many times each driver finished ahead of the other in shared races.
    Optionally restrict to a year range with year_from / year_to.
    """
    result = get_head_to_head(db, driver1_id, driver2_id, year_from, year_to)
    if result is None:
        raise HTTPException(status_code=404, detail="One or both drivers not found")
    return result


@router.get("/drivers/{driver_id}/circuits/{circuit_name}")
def driver_circuit_performance(driver_id: int, circuit_name: str, db: Session = Depends(get_db)):
    """
    A driver's complete historical performance record at a specific circuit.

    Returns appearances, wins, podiums, best finish, average finish position,
    and a season-by-season results breakdown.
    """
    result = get_driver_circuit_performance(db, driver_id, circuit_name)
    if result is None:
        raise HTTPException(status_code=404, detail="No results found for this driver and circuit")
    return result


@router.get("/constructors/era-dominance")
def constructor_era_dominance(db: Session = Depends(get_db)):
    """
    Which constructor dominated each decade of Formula 1 history.

    Groups all race results by decade, sums points per constructor per era,
    and returns the dominant constructor for each decade with win counts.
    """
    return get_constructor_era_dominance(db)


@router.get("/drivers/{driver_id}/win-probability")
def driver_win_probability(
    driver_id: int,
    circuit_name: str | None = Query(default=None, description="Optional circuit name to scope the prediction"),
    db: Session = Depends(get_db),
):
    """
    Estimate a driver's probability of winning at a given circuit.

    Combines four weighted factors into a score between 0 and 1:
    - Circuit win rate (40%) — historical wins at this specific circuit
    - Overall career win rate (30%) — all-time wins across all circuits
    - Recent form (20%) — win rate across the last 10 races
    - Constructor strength (10%) — their constructor's all-time win rate

    When no circuit is specified, overall win rate replaces the circuit factor.
    """
    result = get_win_probability(db, driver_id, circuit_name)
    if result is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return result
