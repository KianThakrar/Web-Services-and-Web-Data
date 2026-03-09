"""Analytics queries — standings, nationality breakdowns, top winners, season summaries,
head-to-head comparisons, circuit performance, and constructor era dominance."""

from sqlalchemy import func, case
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


def _driver_career_stats(db: Session, driver_id: int, year_from: int | None = None, year_to: int | None = None) -> dict | None:
    """Build career stats block for a single driver, optionally restricted to a year range."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None

    query = db.query(RaceResult).filter(RaceResult.driver_id == driver_id)
    if year_from or year_to:
        query = query.join(Race, Race.id == RaceResult.race_id)
        if year_from:
            query = query.filter(Race.season >= year_from)
        if year_to:
            query = query.filter(Race.season <= year_to)
    results = query.all()
    if not results:
        return {
            "driver_id": driver_id,
            "driver_name": driver.name,
            "nationality": driver.nationality,
            "total_races": 0,
            "total_wins": 0,
            "total_points": 0.0,
            "average_finish": None,
            "podiums": 0,
            "dnfs": 0,
        }

    finished = [r for r in results if r.finish_position is not None]
    return {
        "driver_id": driver_id,
        "driver_name": driver.name,
        "nationality": driver.nationality,
        "total_races": len(results),
        "total_wins": sum(1 for r in results if r.finish_position == 1),
        "total_points": float(sum(r.points for r in results)),
        "average_finish": round(sum(r.finish_position for r in finished) / len(finished), 2) if finished else None,
        "podiums": sum(1 for r in results if r.finish_position and r.finish_position <= 3),
        "dnfs": sum(1 for r in results if r.finish_position is None and r.points == 0),
    }


def get_head_to_head(db: Session, driver1_id: int, driver2_id: int, year_from: int | None = None, year_to: int | None = None) -> dict | None:
    """Compare two drivers head-to-head: career stats and direct race comparisons."""
    stats1 = _driver_career_stats(db, driver1_id, year_from, year_to)
    stats2 = _driver_career_stats(db, driver2_id, year_from, year_to)
    if stats1 is None or stats2 is None:
        return None

    # Races where both drivers competed — count who finished ahead
    d1_ahead = 0
    d2_ahead = 0
    q1 = db.query(RaceResult.race_id).filter(RaceResult.driver_id == driver1_id)
    q2 = db.query(RaceResult.race_id).filter(RaceResult.driver_id == driver2_id)
    if year_from or year_to:
        q1 = q1.join(Race, Race.id == RaceResult.race_id)
        q2 = q2.join(Race, Race.id == RaceResult.race_id)
        if year_from:
            q1 = q1.filter(Race.season >= year_from)
            q2 = q2.filter(Race.season >= year_from)
        if year_to:
            q1 = q1.filter(Race.season <= year_to)
            q2 = q2.filter(Race.season <= year_to)
    shared_races = q1.intersect(q2).all()
    for (race_id,) in shared_races:
        r1 = db.query(RaceResult).filter(RaceResult.race_id == race_id, RaceResult.driver_id == driver1_id).first()
        r2 = db.query(RaceResult).filter(RaceResult.race_id == race_id, RaceResult.driver_id == driver2_id).first()
        if r1 and r2:
            p1, p2 = r1.finish_position, r2.finish_position
            if p1 is not None and p2 is not None:
                if p1 < p2:
                    d1_ahead += 1
                elif p2 < p1:
                    d2_ahead += 1
            elif p1 is not None and p2 is None:
                d1_ahead += 1
            elif p2 is not None and p1 is None:
                d2_ahead += 1

    return {
        "driver_1": stats1,
        "driver_2": stats2,
        "head_to_head": {
            "shared_races": len(shared_races),
            "driver_1_ahead": d1_ahead,
            "driver_2_ahead": d2_ahead,
        },
    }


def get_driver_circuit_performance(db: Session, driver_id: int, circuit_name: str) -> dict | None:
    """Return a driver's historical performance record at a specific circuit."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None

    results = (
        db.query(RaceResult)
        .join(Race, Race.id == RaceResult.race_id)
        .filter(RaceResult.driver_id == driver_id, Race.circuit_name == circuit_name)
        .order_by(Race.season)
        .all()
    )
    if not results:
        return None

    finished = [r for r in results if r.finish_position is not None]
    return {
        "driver_id": driver_id,
        "driver_name": driver.name,
        "circuit_name": circuit_name,
        "appearances": len(results),
        "wins": sum(1 for r in results if r.finish_position == 1),
        "podiums": sum(1 for r in results if r.finish_position and r.finish_position <= 3),
        "best_finish": min((r.finish_position for r in finished), default=None),
        "average_finish": round(sum(r.finish_position for r in finished) / len(finished), 2) if finished else None,
        "total_points": float(sum(r.points for r in results)),
        "results_by_season": [
            {
                "season": r.race.season,
                "race_name": r.race.name,
                "finish_position": r.finish_position,
                "position_text": r.position_text,
                "points": r.points,
            }
            for r in results
        ],
    }


def get_win_probability(db: Session, driver_id: int, circuit_name: str | None = None) -> dict | None:
    """Predict win probability using a logistic regression model trained on historical race data.

    Delegates to ml_service which builds features with walk-forward construction
    (no look-ahead bias) and returns a calibrated probability from sklearn.
    """
    from app.services.ml_service import predict_win_probability
    return predict_win_probability(db, driver_id, circuit_name)


def get_constructor_era_dominance(db: Session) -> list[dict]:
    """Rank constructors by total points within each decade era."""
    results = (
        db.query(
            Constructor.name.label("constructor_name"),
            Constructor.nationality,
            func.sum(RaceResult.points).label("total_points"),
            func.count(RaceResult.id).filter(RaceResult.finish_position == 1).label("wins"),
            (func.floor(Race.season / 10) * 10).label("decade"),
        )
        .join(RaceResult, RaceResult.constructor_id == Constructor.id)
        .join(Race, Race.id == RaceResult.race_id)
        .group_by(Constructor.name, Constructor.nationality, (func.floor(Race.season / 10) * 10))
        .order_by((func.floor(Race.season / 10) * 10), func.sum(RaceResult.points).desc())
        .all()
    )

    # For each decade pick the top constructor
    eras: dict[int, dict] = {}
    for r in results:
        decade = int(r.decade)
        era_label = f"{decade}s"
        if decade not in eras:
            eras[decade] = {
                "era": era_label,
                "decade_start": decade,
                "dominant_constructor": r.constructor_name,
                "dominant_constructor_nationality": r.nationality,
                "total_points": float(r.total_points or 0),
                "wins": r.wins or 0,
            }

    return sorted(eras.values(), key=lambda x: x["decade_start"])
