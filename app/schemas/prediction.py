"""Pydantic schemas for Prediction CRUD operations."""

from datetime import datetime
from pydantic import BaseModel


class PredictionCreate(BaseModel):
    race_id: int
    predicted_driver_id: int
    predicted_position: int = 1
    notes: str | None = None


class PredictionUpdate(BaseModel):
    race_id: int
    predicted_driver_id: int
    predicted_position: int = 1
    notes: str | None = None


class PredictionResponse(BaseModel):
    id: int
    race_id: int
    predicted_driver_id: int
    predicted_position: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
