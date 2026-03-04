"""Pydantic schemas for driver read responses."""

from pydantic import BaseModel


class DriverResponse(BaseModel):
    id: int
    driver_ref: str
    name: str
    first_name: str
    last_name: str
    date_of_birth: str | None
    nationality: str
    number: int | None
    code: str | None
    url: str | None

    model_config = {"from_attributes": True}
