"""Race read endpoints — list with season filtering and individual lookup."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.race import Race
from app.schemas.race import RaceResponse

router = APIRouter(prefix="/api/v1/races", tags=["Races"])


@router.get("", response_model=list[RaceResponse])
def list_races(
    season: int | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """List all races, optionally filtered by season."""
    query = db.query(Race)
    if season:
        query = query.filter(Race.season == season)
    return query.order_by(Race.season, Race.round).offset(offset).limit(limit).all()


@router.get("/{race_id}", response_model=RaceResponse)
def get_race(race_id: int, db: Session = Depends(get_db)):
    """Retrieve a single race by ID."""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race
