"""Pydantic schemas for constructor read responses."""

from pydantic import BaseModel


class ConstructorResponse(BaseModel):
    id: int
    constructor_ref: str
    name: str
    nationality: str
    url: str | None

    model_config = {"from_attributes": True}
