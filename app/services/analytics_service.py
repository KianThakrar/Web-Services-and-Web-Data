"""Analytics queries — standings, nationality breakdowns, top winners, and season summaries."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult


def get_constructor_standings(db: Session, season: int) -> list[dict]:
    """Rank constructors by total points for a given season."""
    results = (
        db.query(
            Constructor.id,
            Constructor.name.label("constructor_name"),
            Constructor.nationality,
            func.sum(RaceResult.points).label("total_points"),
            func.count(RaceResult.id).filter(RaceResult.finish_position == 1).label("wins"),
        )
        .join(RaceResult, RaceResult.constructor_id == Constructor.id)
        .join(Race, Race.id == RaceResult.race_id)
        .filter(Race.season == season)
        .group_by(Constructor.id, Constructor.name, Constructor.nationality)
        .order_by(func.sum(RaceResult.points).desc())
        .all()
    )
    return [
        {
            "constructor_id": r.id,
            "constructor_name": r.constructor_name,
            "nationality": r.nationality,
            "total_points": float(r.total_points or 0),
            "wins": r.wins or 0,
        }
        for r in results
    ]


def get_driver_standings(db: Session, season: int) -> list[dict]:
    """Rank drivers by total points for a given season."""
    results = (
        db.query(
            Driver.id,
            Driver.name.label("driver_name"),
            Driver.nationality,
            func.sum(RaceResult.points).label("total_points"),
            func.count(RaceResult.id).filter(RaceResult.finish_position == 1).label("wins"),
        )
        .join(RaceResult, RaceResult.driver_id == Driver.id)
        .join(Race, Race.id == RaceResult.race_id)
        .filter(Race.season == season)
        .group_by(Driver.id, Driver.name, Driver.nationality)
        .order_by(func.sum(RaceResult.points).desc())
        .all()
    )
    return [
        {
            "driver_id": r.id,
            "driver_name": r.driver_name,
            "nationality": r.nationality,
            "total_points": float(r.total_points or 0),
            "wins": r.wins or 0,
        }
        for r in results
    ]


def get_driver_nationality_breakdown(db: Session) -> list[dict]:
    """Count drivers by nationality across all seasons."""
    results = (
        db.query(Driver.nationality, func.count(Driver.id).label("count"))
        .group_by(Driver.nationality)
        .order_by(func.count(Driver.id).desc())
        .all()
    )
    return [{"nationality": r.nationality, "count": r.count} for r in results]


def get_top_race_winners(db: Session, limit: int = 10) -> list[dict]:
    """Return drivers ranked by total race wins across all time."""
    results = (
        db.query(
            Driver.id,
            Driver.name.label("driver_name"),
            Driver.nationality,
            func.count(RaceResult.id).label("wins"),
        )
        .join(RaceResult, RaceResult.driver_id == Driver.id)
        .filter(RaceResult.finish_position == 1)
        .group_by(Driver.id, Driver.name, Driver.nationality)
        .order_by(func.count(RaceResult.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "driver_id": r.id,
            "driver_name": r.driver_name,
            "nationality": r.nationality,
            "wins": r.wins,
        }
        for r in results
    ]


def get_season_summary(db: Session, season: int) -> dict:
    """Return high-level statistics for a given season."""
    total_races = db.query(func.count(Race.id)).filter(Race.season == season).scalar() or 0
    drivers_competed = (
        db.query(func.count(func.distinct(RaceResult.driver_id)))
        .join(Race, Race.id == RaceResult.race_id)
        .filter(Race.season == season)
        .scalar() or 0
    )
    constructors_competed = (
        db.query(func.count(func.distinct(RaceResult.constructor_id)))
        .join(Race, Race.id == RaceResult.race_id)
        .filter(Race.season == season)
        .scalar() or 0
    )
    total_points = (
        db.query(func.sum(RaceResult.points))
        .join(Race, Race.id == RaceResult.race_id)
        .filter(Race.season == season)
        .scalar() or 0
    )
    return {
        "season": season,
        "total_races": total_races,
        "drivers_competed": drivers_competed,
        "constructors_competed": constructors_competed,
        "total_points_awarded": float(total_points),
    }
