"""Driver read endpoints — list with filtering and individual lookup."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.driver import Driver
from app.schemas.driver import DriverResponse

router = APIRouter(prefix="/api/v1/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverResponse])
def list_drivers(nationality: str | None = None, db: Session = Depends(get_db)):
    """List all drivers, optionally filtered by nationality."""
    query = db.query(Driver)
    if nationality:
        query = query.filter(Driver.nationality == nationality)
    return query.order_by(Driver.last_name).all()


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Retrieve a single driver by ID."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver
