"""Driver read endpoints — list with filtering and individual lookup."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.driver import Driver
from app.schemas.driver import DriverResponse

router = APIRouter(prefix="/api/v1/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverResponse])
def list_drivers(
    nationality: str | None = None,
    name: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """List all drivers, optionally filtered by nationality or partial name."""
    query = db.query(Driver)
    if nationality:
        query = query.filter(Driver.nationality == nationality)
    if name:
        query = query.filter(Driver.name.ilike(f"%{name}%"))
    return query.order_by(Driver.last_name).offset(offset).limit(limit).all()


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Retrieve a single driver by ID."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver
