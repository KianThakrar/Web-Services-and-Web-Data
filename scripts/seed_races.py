"""Seed races and race results from Jolpica F1 API for key seasons."""

import httpx
from sqlalchemy.orm import Session

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

# Seed these seasons for a rich dataset covering multiple eras
SEASONS_TO_SEED = [2020, 2021, 2022, 2023, 2024]


def fetch_season_races(season: int) -> list[dict]:
    """Fetch all races for a season by paginating through rounds."""
    races = []
    offset = 0
    limit = 30

    while True:
        url = f"{JOLPICA_BASE}/{season}/results.json?limit={limit}&offset={offset}"
        response = httpx.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        batch = data["MRData"]["RaceTable"]["Races"]
        if not batch:
            break
        races.extend(batch)
        total = int(data["MRData"]["total"])
        offset += limit
        if offset >= total:
            break

    return races


def seed_races(db: Session) -> int:
    """Seed races and results for configured seasons. Returns total races seeded."""
    total_races = 0
    total_results = 0

    for season in SEASONS_TO_SEED:
        print(f"\nSeeding season {season}...")
        races_data = fetch_season_races(season)

        for race_data in races_data:
            circuit = race_data["Circuit"]
            existing_race = db.query(Race).filter(
                Race.season == int(race_data["season"]),
                Race.round == int(race_data["round"]),
            ).first()

            if not existing_race:
                race = Race(
                    season=int(race_data["season"]),
                    round=int(race_data["round"]),
                    name=race_data["raceName"],
                    circuit_name=circuit["circuitName"],
                    circuit_location=circuit["Location"]["locality"],
                    circuit_country=circuit["Location"]["country"],
                    date=race_data.get("date"),
                    url=race_data.get("url"),
                )
                db.add(race)
                db.flush()
                race_id = race.id
                total_races += 1
            else:
                race_id = existing_race.id

            for result in race_data.get("Results", []):
                driver_ref = result["Driver"]["driverId"]
                constructor_ref = result["Constructor"]["constructorId"]

                driver = db.query(Driver).filter(Driver.driver_ref == driver_ref).first()
                constructor = db.query(Constructor).filter(
                    Constructor.constructor_ref == constructor_ref
                ).first()

                if not driver or not constructor:
                    continue

                existing_result = db.query(RaceResult).filter(
                    RaceResult.race_id == race_id,
                    RaceResult.driver_id == driver.id,
                ).first()

                if existing_result:
                    continue

                race_result = RaceResult(
                    race_id=race_id,
                    driver_id=driver.id,
                    constructor_id=constructor.id,
                    grid_position=int(result.get("grid", 0)) or None,
                    finish_position=int(result["position"]) if result.get("position", "").isdigit() else None,
                    position_text=result.get("positionText"),
                    points=float(result.get("points", 0)),
                    laps=int(result.get("laps", 0)) or None,
                    status=result.get("status"),
                    fastest_lap_time=(
                        result["FastestLap"]["Time"]["time"]
                        if result.get("FastestLap") and result["FastestLap"].get("Time")
                        else None
                    ),
                )
                db.add(race_result)
                total_results += 1

        db.commit()
        print(f"  Season {season}: {len(races_data)} races processed.")

    print(f"\nTotal: {total_races} new races, {total_results} new results seeded.")
    return total_races
