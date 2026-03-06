"""Favourite CRUD endpoints — auth-protected driver bookmarking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user
from app.database import get_db
from app.models.driver import Driver
from app.models.favourite import Favourite
from app.models.user import User
from app.schemas.favourite import FavouriteCreate, FavouriteResponse

router = APIRouter(prefix="/api/v1/favourites", tags=["Favourites"])


@router.post("", response_model=FavouriteResponse, status_code=status.HTTP_201_CREATED)
def add_favourite(
    data: FavouriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a driver to the authenticated user's favourites."""
    if not db.query(Driver).filter(Driver.id == data.driver_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    existing = db.query(Favourite).filter(
        Favourite.user_id == current_user.id,
        Favourite.driver_id == data.driver_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Driver already in favourites")

    favourite = Favourite(user_id=current_user.id, driver_id=data.driver_id)
    db.add(favourite)
    db.commit()
    db.refresh(favourite)
    return favourite


@router.get("", response_model=list[FavouriteResponse])
def list_favourites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all favourite drivers for the authenticated user."""
    return db.query(Favourite).filter(Favourite.user_id == current_user.id).all()


@router.delete("/{favourite_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favourite(
    favourite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a driver from the authenticated user's favourites."""
    favourite = db.query(Favourite).filter(
        Favourite.id == favourite_id,
        Favourite.user_id == current_user.id,
    ).first()
    if not favourite:
        raise HTTPException(status_code=404, detail="Favourite not found")

    db.delete(favourite)
    db.commit()
