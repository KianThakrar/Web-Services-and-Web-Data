"""Pydantic schemas for Prediction CRUD operations."""

from datetime import datetime
from pydantic import BaseModel, Field


class PredictionCreate(BaseModel):
    race_id: int = Field(gt=0)
    predicted_driver_id: int = Field(gt=0)
    predicted_position: int = Field(default=1, ge=1, le=30)
    notes: str | None = None


class PredictionUpdate(BaseModel):
    race_id: int = Field(gt=0)
    predicted_driver_id: int = Field(gt=0)
    predicted_position: int = Field(default=1, ge=1, le=30)
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
