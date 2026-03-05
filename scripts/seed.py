"""Master seed script — run this once after database setup to populate all F1 data.

Usage:
    python -m scripts.seed
    python -m scripts.seed --reset   # drop and recreate tables before seeding
"""

import argparse
import sys

from app.database import Base, SessionLocal, engine
from scripts.seed_constructors import seed_constructors
from scripts.seed_drivers import seed_drivers
from scripts.seed_races import seed_races


def run(reset: bool = False) -> None:
    print("=== F1 Racing Intelligence API — Data Seed ===")
    print("Fetching data from Jolpica F1 API. This takes ~60 seconds on first run.\n")

    if reset:
        print("Dropping and recreating all tables...")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

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
    args = parser.parse_args()
    run(reset=args.reset)
