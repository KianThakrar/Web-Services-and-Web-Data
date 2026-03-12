"""Analytics endpoints — aggregated F1 statistics and insights."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
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
from app.services.ml_service import predict_race_win_probabilities
from app.services.weather_service import (
    get_circuit_weather_profile,
    get_driver_weather_performance,
    get_race_weather_impact,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/constructors/standings")
def constructor_standings(
    season: int = Query(..., ge=1950, le=2100),
    db: Session = Depends(get_db),
):
    """Return constructor championship standings for a season, ranked by points."""
    return get_constructor_standings(db, season)


@router.get("/drivers/standings")
def driver_standings(
    season: int = Query(..., ge=1950, le=2100),
    db: Session = Depends(get_db),
):
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
def season_summary(
    season: int = Path(..., ge=1950, le=2100),
    db: Session = Depends(get_db),
):
    """Return a high-level statistical summary for a given season."""
    return get_season_summary(db, season)


@router.get("/drivers/{driver1_id}/vs/{driver2_id}")
def head_to_head(
    driver1_id: int = Path(..., gt=0),
    driver2_id: int = Path(..., gt=0),
    year_from: int | None = Query(default=None, ge=1950, le=2100),
    year_to: int | None = Query(default=None, ge=1950, le=2100),
    db: Session = Depends(get_db),
):
    """
    Head-to-head career comparison between two drivers.

    Returns full career stats for each driver plus direct race comparisons —
    how many times each driver finished ahead of the other in shared races.
    Optionally restrict to a year range with year_from / year_to.
    """
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(status_code=400, detail="year_from must be less than or equal to year_to")
    result = get_head_to_head(db, driver1_id, driver2_id, year_from, year_to)
    if result is None:
        raise HTTPException(status_code=404, detail="One or both drivers not found")
    return result


@router.get("/drivers/{driver_id}/circuits/{circuit_name}")
def driver_circuit_performance(
    driver_id: int = Path(..., gt=0),
    circuit_name: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
):
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


@router.get("/races/{race_id}/win-probabilities")
def race_win_probabilities(
    race_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    Independent win probabilities for every driver in a race.

    Computes each driver's logistic regression win probability independently —
    P(driver wins) given their career features at this circuit. Probabilities
    are not normalised and will not sum to 1.0; each is an honest per-driver
    binary prediction. Returns drivers sorted by probability descending.
    """
    result = predict_race_win_probabilities(db, race_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Race not found or has no results")
    return result


@router.get("/drivers/{driver_id}/win-probability")
def driver_win_probability(
    driver_id: int = Path(..., gt=0),
    circuit_name: str | None = Query(default=None, description="Optional circuit name to scope the prediction"),
    db: Session = Depends(get_db),
):
    """
    Estimate a driver's probability of winning at a given circuit.

    Uses a logistic regression model trained on historical race results with
    walk-forward feature construction (no look-ahead bias). The model combines:
    - decayed career win rate
    - Bayesian-smoothed circuit win rate
    - recent points form (last 10 races)
    - constructor form (last 3 seasons)

    Returns the calibrated probability plus factor-level diagnostics.
    """
    result = get_win_probability(db, driver_id, circuit_name)
    if result is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return result


# ---------------------------------------------------------------------------
# Weather × Performance endpoints
# ---------------------------------------------------------------------------


@router.get("/weather/circuits/{circuit_name}")
def circuit_weather_profile(
    circuit_name: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Weather profile for an F1 circuit — average temperature, rain frequency,
    and common conditions across all historical races at the circuit.

    Uses data from the Open-Meteo Archive API, pre-fetched and stored as CSV.
    """
    result = get_circuit_weather_profile(db, circuit_name)
    if result is None:
        raise HTTPException(status_code=404, detail="No weather data found for this circuit")
    return result


@router.get("/weather/drivers/{driver_id}")
def driver_weather_performance(
    driver_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    How a driver performs in wet vs dry conditions.

    Splits the driver's race history into wet and dry races based on WMO
    weather codes and precipitation data, then compares win rate, podium rate,
    and average finishing position across conditions.
    """
    result = get_driver_weather_performance(db, driver_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return result


@router.get("/weather/races/{race_id}")
def race_weather_impact(
    race_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    Weather conditions and full driver results for a specific race.

    Returns temperature, precipitation, wind speed, and WMO condition
    classification alongside the complete race results — allowing analysis
    of how weather influenced finishing positions.
    """
    result = get_race_weather_impact(db, race_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return result
