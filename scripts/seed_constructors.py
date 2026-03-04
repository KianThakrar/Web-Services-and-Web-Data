"""Seed constructors (teams) from Jolpica F1 API."""

import httpx
from sqlalchemy.orm import Session

from app.models.constructor import Constructor

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"


def fetch_all_constructors() -> list[dict]:
    """Fetch all constructors from Jolpica API."""
    constructors = []
    offset = 0
    limit = 100

    print("Fetching constructors from Jolpica API...")
    while True:
        url = f"{JOLPICA_BASE}/constructors.json?limit={limit}&offset={offset}"
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        batch = data["MRData"]["ConstructorTable"]["Constructors"]
        if not batch:
            break

        constructors.extend(batch)
        total = int(data["MRData"]["total"])
        offset += limit
        print(f"  Fetched {min(offset, total)}/{total} constructors")

        if offset >= total:
            break

    return constructors


def seed_constructors(db: Session) -> int:
    """Upsert all constructors into the database. Returns count seeded."""
    raw = fetch_all_constructors()
    seeded = 0

    for c in raw:
        existing = db.query(Constructor).filter(
            Constructor.constructor_ref == c["constructorId"]
        ).first()
        if existing:
            continue

        constructor = Constructor(
            constructor_ref=c["constructorId"],
            name=c["name"],
            nationality=c.get("nationality", "Unknown"),
            url=c.get("url"),
        )
        db.add(constructor)
        seeded += 1

    db.commit()
    print(f"  Seeded {seeded} new constructors.")
    return seeded
