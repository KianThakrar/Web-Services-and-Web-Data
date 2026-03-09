"""Seed drivers from Jolpica F1 API (Ergast-compatible)."""

from datetime import date

import httpx
from sqlalchemy.orm import Session

from app.models.driver import Driver

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def fetch_all_drivers() -> list[dict]:
    """Fetch all drivers across all seasons from Jolpica API."""
    drivers = []
    offset = 0
    limit = 100

    print("Fetching drivers from Jolpica API...")
    while True:
        url = f"{JOLPICA_BASE}/drivers.json?limit={limit}&offset={offset}"
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        batch = data["MRData"]["DriverTable"]["Drivers"]
        if not batch:
            break

        drivers.extend(batch)
        total = int(data["MRData"]["total"])
        offset += limit
        print(f"  Fetched {min(offset, total)}/{total} drivers")

        if offset >= total:
            break

    return drivers


def seed_drivers(db: Session) -> int:
    """Upsert all drivers into the database. Returns count of drivers seeded."""
    raw = fetch_all_drivers()
    seeded = 0

    for d in raw:
        existing = db.query(Driver).filter(Driver.driver_ref == d["driverId"]).first()
        if existing:
            continue

        driver = Driver(
            driver_ref=d["driverId"],
            name=f"{d['givenName']} {d['familyName']}",
            first_name=d["givenName"],
            last_name=d["familyName"],
            date_of_birth=_parse_date(d.get("dateOfBirth")),
            nationality=d.get("nationality", "Unknown"),
            number=int(d["permanentNumber"]) if d.get("permanentNumber") else None,
            code=d.get("code"),
            url=d.get("url"),
        )
        db.add(driver)
        seeded += 1

    db.commit()
    print(f"  Seeded {seeded} new drivers.")
    return seeded
