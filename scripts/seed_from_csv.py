"""Seed the database from pre-built CSV files in data/csv/.

This is the fast path — no external API calls required.
The CSVs are included in the repository so the assessor can populate
the database without needing internet access to Jolpica/Ergast.

Usage:
    python -m scripts.seed_from_csv
"""

import csv
import os
import sys

from app.database import Base, SessionLocal, engine
from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.race import Race
from app.models.race_result import RaceResult

CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "csv")


def _read(filename: str) -> list[dict]:
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        print(f"  ERROR: {path} not found.")
        sys.exit(1)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _int(val: str) -> int | None:
    return int(val) if val not in ("", "None", None) else None


def _float(val: str) -> float | None:
    return float(val) if val not in ("", "None", None) else None


def _str(val: str) -> str | None:
    return val if val not in ("", "None", None) else None


def run() -> None:
    print("=== F1 Racing Intelligence API — CSV Seed ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ── Drivers ──────────────────────────────────────────────────────────
        print("\n[1/4] Loading drivers...")
        rows = _read("drivers.csv")
        inserted = 0
        for r in rows:
            if db.query(Driver).filter(Driver.id == int(r["id"])).first():
                continue
            db.add(Driver(
                id=int(r["id"]),
                driver_ref=r["driver_ref"],
                name=r["name"],
                first_name=_str(r["first_name"]),
                last_name=_str(r["last_name"]),
                date_of_birth=_str(r["date_of_birth"]),
                nationality=_str(r["nationality"]),
                number=_int(r["number"]),
                code=_str(r["code"]),
                url=_str(r["url"]),
            ))
            inserted += 1
        db.commit()
        print(f"  {inserted} drivers inserted ({len(rows) - inserted} already existed).")

        # ── Constructors ─────────────────────────────────────────────────────
        print("\n[2/4] Loading constructors...")
        rows = _read("constructors.csv")
        inserted = 0
        for r in rows:
            if db.query(Constructor).filter(Constructor.id == int(r["id"])).first():
                continue
            db.add(Constructor(
                id=int(r["id"]),
                constructor_ref=r["constructor_ref"],
                name=r["name"],
                nationality=_str(r["nationality"]),
                url=_str(r["url"]),
            ))
            inserted += 1
        db.commit()
        print(f"  {inserted} constructors inserted ({len(rows) - inserted} already existed).")

        # ── Races ────────────────────────────────────────────────────────────
        print("\n[3/4] Loading races...")
        rows = _read("races.csv")
        inserted = 0
        for r in rows:
            if db.query(Race).filter(Race.id == int(r["id"])).first():
                continue
            db.add(Race(
                id=int(r["id"]),
                season=int(r["season"]),
                round=int(r["round"]),
                name=r["name"],
                circuit_name=_str(r["circuit_name"]),
                circuit_location=_str(r["circuit_location"]),
                circuit_country=_str(r["circuit_country"]),
                date=_str(r["date"]),
                url=_str(r["url"]),
            ))
            inserted += 1
        db.commit()
        print(f"  {inserted} races inserted ({len(rows) - inserted} already existed).")

        # ── Race results ─────────────────────────────────────────────────────
        print("\n[4/4] Loading race results...")
        rows = _read("race_results.csv")
        inserted = 0
        batch = []
        for i, r in enumerate(rows):
            if db.query(RaceResult).filter(RaceResult.id == int(r["id"])).first():
                continue
            batch.append(RaceResult(
                id=int(r["id"]),
                race_id=int(r["race_id"]),
                driver_id=int(r["driver_id"]),
                constructor_id=int(r["constructor_id"]),
                grid_position=_int(r["grid_position"]),
                finish_position=_int(r["finish_position"]),
                position_text=_str(r["position_text"]),
                points=_float(r["points"]) or 0.0,
                laps=_int(r["laps"]),
                status=_str(r["status"]),
                fastest_lap_time=_str(r["fastest_lap_time"]),
            ))
            inserted += 1
            if len(batch) >= 500:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
                print(f"  ...{i + 1}/{len(rows)} rows processed", end="\r")
        if batch:
            db.bulk_save_objects(batch)
            db.commit()
        print(f"\n  {inserted} results inserted ({len(rows) - inserted} already existed).")

        print("\n✓ CSV seed complete.")
    except Exception as e:
        print(f"\n✗ Seed failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run()
