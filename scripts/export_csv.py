"""Export the current database tables to CSV files in data/csv/.

Run this once after seeding to produce portable CSV snapshots.

Usage:
    python -m scripts.export_csv
"""

import csv
import os

from app.database import SessionLocal
from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "csv")


def _write(filename: str, rows: list[dict]) -> None:
    if not rows:
        print(f"  {filename}: no rows, skipping.")
        return
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows):,} rows written → {path}")


def run() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    db = SessionLocal()
    try:
        print("Exporting drivers...")
        _write("drivers.csv", [
            {
                "id": d.id, "driver_ref": d.driver_ref, "name": d.name,
                "first_name": d.first_name, "last_name": d.last_name,
                "date_of_birth": d.date_of_birth, "nationality": d.nationality,
                "number": d.number, "code": d.code, "url": d.url,
            }
            for d in db.query(Driver).order_by(Driver.id).all()
        ])

        print("Exporting constructors...")
        _write("constructors.csv", [
            {
                "id": c.id, "constructor_ref": c.constructor_ref,
                "name": c.name, "nationality": c.nationality, "url": c.url,
            }
            for c in db.query(Constructor).order_by(Constructor.id).all()
        ])

        print("Exporting races...")
        _write("races.csv", [
            {
                "id": r.id, "season": r.season, "round": r.round, "name": r.name,
                "circuit_name": r.circuit_name, "circuit_location": r.circuit_location,
                "circuit_country": r.circuit_country, "date": r.date, "url": r.url,
            }
            for r in db.query(Race).order_by(Race.season, Race.round).all()
        ])

        print("Exporting race results...")
        _write("race_results.csv", [
            {
                "id": rr.id, "race_id": rr.race_id, "driver_id": rr.driver_id,
                "constructor_id": rr.constructor_id, "grid_position": rr.grid_position,
                "finish_position": rr.finish_position, "position_text": rr.position_text,
                "points": rr.points, "laps": rr.laps, "status": rr.status,
                "fastest_lap_time": rr.fastest_lap_time,
            }
            for rr in db.query(RaceResult).order_by(RaceResult.id).all()
        ])

        print(f"\nDone. CSVs written to {OUT_DIR}/")
    finally:
        db.close()


if __name__ == "__main__":
    run()
