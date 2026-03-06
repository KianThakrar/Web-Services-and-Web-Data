"""Prediction CRUD endpoints — auth-protected race outcome predictions."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user
from app.database import get_db
from app.models.driver import Driver
from app.models.prediction import Prediction
from app.models.race import Race
from app.models.user import User
from app.schemas.prediction import PredictionCreate, PredictionResponse, PredictionUpdate

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(
    data: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new race outcome prediction for the authenticated user."""
    if not db.query(Race).filter(Race.id == data.race_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    if not db.query(Driver).filter(Driver.id == data.predicted_driver_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    prediction = Prediction(
        user_id=current_user.id,
        race_id=data.race_id,
        predicted_driver_id=data.predicted_driver_id,
        predicted_position=data.predicted_position,
        notes=data.notes,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.get("", response_model=list[PredictionResponse])
def list_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all predictions made by the authenticated user."""
    return db.query(Prediction).filter(Prediction.user_id == current_user.id).all()


@router.put("/{prediction_id}", response_model=PredictionResponse)
def update_prediction(
    prediction_id: int,
    data: PredictionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing prediction owned by the authenticated user."""
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    if prediction.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this prediction")

    if not db.query(Race).filter(Race.id == data.race_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    if not db.query(Driver).filter(Driver.id == data.predicted_driver_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    prediction.race_id = data.race_id
    prediction.predicted_driver_id = data.predicted_driver_id
    prediction.predicted_position = data.predicted_position
    prediction.notes = data.notes
    prediction.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a prediction owned by the authenticated user."""
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    if prediction.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this prediction")

    db.delete(prediction)
    db.commit()
