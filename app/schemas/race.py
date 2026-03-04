"""Pydantic schemas for race read responses."""

from pydantic import BaseModel


class RaceResponse(BaseModel):
    id: int
    season: int
    round: int
    name: str
    circuit_name: str
    circuit_location: str | None
    circuit_country: str | None
    date: str | None
    url: str | None

    model_config = {"from_attributes": True}
