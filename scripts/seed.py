"""Master seed script — run this once after database setup to populate all F1 data.

Prefers loading from local CSV files (data/csv/) for speed and reliability.
Falls back to fetching from the Jolpica F1 API if CSVs are not present.

Usage:
    python -m scripts.seed
    python -m scripts.seed --reset   # drop and recreate tables before seeding
    python -m scripts.seed --api     # force fetch from Jolpica API even if CSVs exist
"""

import argparse
import os
import sys

from app.database import Base, engine

CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "csv")
_CSV_FILES = ["drivers.csv", "constructors.csv", "races.csv", "race_results.csv"]


def _csvs_available() -> bool:
    return all(os.path.exists(os.path.join(CSV_DIR, f)) for f in _CSV_FILES)


def run(reset: bool = False, force_api: bool = False) -> None:
    print("=== F1 Racing Intelligence API — Data Seed ===")

    if reset:
        print("Dropping and recreating all tables...")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    if not force_api and _csvs_available():
        print("CSV files found — seeding from data/csv/ (fast, no API calls needed).\n")
        from scripts.seed_from_csv import run as csv_run
        csv_run()
        return

    print("No CSV files found — fetching data from Jolpica F1 API.\n")
    from app.database import SessionLocal
    from scripts.seed_constructors import seed_constructors
    from scripts.seed_drivers import seed_drivers
    from scripts.seed_races import seed_races

    db = SessionLocal()
    try:
        print("[1/3] Seeding drivers...")
        seed_drivers(db)

        print("\n[2/3] Seeding constructors...")
        seed_constructors(db)

        print("\n[3/3] Seeding races and results...")
        seed_races(db)

        print("\n✓ Seed complete.")
    except Exception as e:
        print(f"\n✗ Seed failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed F1 data into PostgreSQL")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables before seeding")
    parser.add_argument("--api", action="store_true", help="Force fetch from Jolpica API even if CSVs exist")
    args = parser.parse_args()
    run(reset=args.reset, force_api=args.api)
