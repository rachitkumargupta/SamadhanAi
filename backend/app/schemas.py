from datetime import datetime

from pydantic import BaseModel, ConfigDict, StringConstraints
from typing import Annotated


ComplaintDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
]
LocationText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: ComplaintDescription
    location_text: LocationText | None = None


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_reference: str
    description: str
    location_text: str | None
    status: str
    created_at: datetime


class ComplaintListPage(BaseModel):
    items: list[ComplaintRead]
    limit: int
    offset: int
    next_offset: int | None


class ComplaintEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_type: str
    occurred_at: datetime


class ComplaintEventPage(BaseModel):
    items: list[ComplaintEventRead]
    limit: int
    offset: int
    next_offset: int | None
