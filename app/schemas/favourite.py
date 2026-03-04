"""Pydantic schemas for Favourite CRUD operations."""

from datetime import datetime
from pydantic import BaseModel


class FavouriteCreate(BaseModel):
    driver_id: int


class FavouriteResponse(BaseModel):
    id: int
    driver_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
