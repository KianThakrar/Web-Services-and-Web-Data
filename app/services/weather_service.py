"""Weather analytics service — correlates Open-Meteo weather data with F1 race results.

All weather data is read from the WeatherCache table (seeded from CSV).
No external API calls are made at runtime.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult
from app.models.weather_cache import WeatherCache

# WMO weather codes: 0-3 = clear/cloudy, 45-48 = fog,
# 51-57 = drizzle, 61-67 = rain, 71-77 = snow, 80-82 = showers, 85-86 = snow showers, 95-99 = thunderstorm
_WET_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}

WMO_DESCRIPTIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _is_wet(weather: WeatherCache) -> bool:
    """Return True if the weather conditions classify as wet."""
    if weather.weather_code is not None and weather.weather_code in _WET_CODES:
        return True
    if weather.precipitation_mm is not None and weather.precipitation_mm > 0.5:
        return True
    return False


def get_circuit_weather_profile(db: Session, circuit_name: str) -> dict | None:
    """Aggregate weather statistics across all races at a given circuit."""
    races_with_weather = (
        db.query(Race, WeatherCache)
        .join(WeatherCache, WeatherCache.race_id == Race.id)
        .filter(Race.circuit_name == circuit_name)
        .order_by(Race.season)
        .all()
    )

    if not races_with_weather:
        return None

    temps_max = [w.temperature_max for _, w in races_with_weather if w.temperature_max is not None]
    temps_min = [w.temperature_min for _, w in races_with_weather if w.temperature_min is not None]
    precips = [w.precipitation_mm for _, w in races_with_weather if w.precipitation_mm is not None]
    winds = [w.wind_speed_max for _, w in races_with_weather if w.wind_speed_max is not None]
    wet_count = sum(1 for _, w in races_with_weather if _is_wet(w))
    total = len(races_with_weather)

    # Weather code frequency
    code_freq: dict[str, int] = {}
    for _, w in races_with_weather:
        desc = WMO_DESCRIPTIONS.get(w.weather_code, f"Code {w.weather_code}")
        code_freq[desc] = code_freq.get(desc, 0) + 1

    return {
        "circuit_name": circuit_name,
        "total_races_with_data": total,
        "avg_temperature_max": round(sum(temps_max) / len(temps_max), 1) if temps_max else None,
        "avg_temperature_min": round(sum(temps_min) / len(temps_min), 1) if temps_min else None,
        "avg_precipitation_mm": round(sum(precips) / len(precips), 1) if precips else None,
        "max_precipitation_mm": round(max(precips), 1) if precips else None,
        "avg_wind_speed_max": round(sum(winds) / len(winds), 1) if winds else None,
        "wet_race_percentage": round((wet_count / total) * 100, 1) if total else 0,
        "wet_races": wet_count,
        "dry_races": total - wet_count,
        "common_conditions": dict(sorted(code_freq.items(), key=lambda x: x[1], reverse=True)),
        "race_history": [
            {
                "season": race.season,
                "race_name": race.name,
                "date": race.date,
                "temperature_max": w.temperature_max,
                "temperature_min": w.temperature_min,
                "precipitation_mm": w.precipitation_mm,
                "wind_speed_max": w.wind_speed_max,
                "condition": WMO_DESCRIPTIONS.get(w.weather_code, f"Code {w.weather_code}"),
                "is_wet": _is_wet(w),
            }
            for race, w in races_with_weather
        ],
    }


def get_driver_weather_performance(db: Session, driver_id: int) -> dict | None:
    """Compare a driver's performance in wet vs dry conditions."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None

    # Get all results with weather data for this driver
    rows = (
        db.query(RaceResult, WeatherCache)
        .join(Race, Race.id == RaceResult.race_id)
        .join(WeatherCache, WeatherCache.race_id == Race.id)
        .filter(RaceResult.driver_id == driver_id)
        .all()
    )

    if not rows:
        return {
            "driver_id": driver_id,
            "driver_name": driver.name,
            "total_races_with_weather_data": 0,
            "wet": None,
            "dry": None,
            "verdict": "Insufficient weather data",
        }

    wet_results = [r for r, w in rows if _is_wet(w)]
    dry_results = [r for r, w in rows if not _is_wet(w)]

    def _stats(results: list[RaceResult], label: str) -> dict:
        if not results:
            return {"condition": label, "races": 0, "wins": 0, "podiums": 0, "win_rate": 0, "avg_finish": None}
        finished = [r for r in results if r.finish_position is not None]
        wins = sum(1 for r in results if r.finish_position == 1)
        podiums = sum(1 for r in results if r.finish_position and r.finish_position <= 3)
        avg = round(sum(r.finish_position for r in finished) / len(finished), 2) if finished else None
        return {
            "condition": label,
            "races": len(results),
            "wins": wins,
            "podiums": podiums,
            "win_rate": round(wins / len(results), 4) if results else 0,
            "podium_rate": round(podiums / len(results), 4) if results else 0,
            "avg_finish": avg,
            "dnfs": len(results) - len(finished),
            "total_points": float(sum(r.points for r in results)),
        }

    wet_stats = _stats(wet_results, "Wet")
    dry_stats = _stats(dry_results, "Dry")

    # Generate a human-readable verdict
    if wet_stats["races"] < 3:
        verdict = "Not enough wet races for a reliable comparison"
    elif wet_stats["avg_finish"] is not None and dry_stats["avg_finish"] is not None:
        diff = dry_stats["avg_finish"] - wet_stats["avg_finish"]
        if diff > 1.5:
            verdict = f"{driver.name} is a rain specialist — finishes {abs(diff):.1f} places higher in wet conditions"
        elif diff < -1.5:
            verdict = f"{driver.name} struggles in wet conditions — finishes {abs(diff):.1f} places lower"
        else:
            verdict = f"{driver.name} performs consistently regardless of weather conditions"
    else:
        verdict = "Mixed results across conditions"

    return {
        "driver_id": driver_id,
        "driver_name": driver.name,
        "nationality": driver.nationality,
        "total_races_with_weather_data": len(rows),
        "wet": wet_stats,
        "dry": dry_stats,
        "verdict": verdict,
    }


def get_race_weather_impact(db: Session, race_id: int) -> dict | None:
    """Return weather conditions and full driver results for a specific race."""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        return None

    weather = db.query(WeatherCache).filter(WeatherCache.race_id == race_id).first()
    if not weather:
        return {
            "race_id": race_id,
            "race_name": race.name,
            "season": race.season,
            "circuit_name": race.circuit_name,
            "date": race.date,
            "weather": None,
            "results": [],
        }

    results = (
        db.query(RaceResult, Driver)
        .join(Driver, Driver.id == RaceResult.driver_id)
        .filter(RaceResult.race_id == race_id)
        .order_by(RaceResult.finish_position.asc().nullslast())
        .all()
    )

    return {
        "race_id": race_id,
        "race_name": race.name,
        "season": race.season,
        "circuit_name": race.circuit_name,
        "date": race.date,
        "weather": {
            "temperature_max": weather.temperature_max,
            "temperature_min": weather.temperature_min,
            "precipitation_mm": weather.precipitation_mm,
            "wind_speed_max": weather.wind_speed_max,
            "condition": WMO_DESCRIPTIONS.get(weather.weather_code, f"Code {weather.weather_code}"),
            "weather_code": weather.weather_code,
            "is_wet": _is_wet(weather),
        },
        "results": [
            {
                "position": r.finish_position,
                "position_text": r.position_text,
                "driver_id": r.driver_id,
                "driver_name": d.name,
                "grid_position": r.grid_position,
                "points": r.points,
                "status": r.status,
            }
            for r, d in results
        ],
    }
