
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class IncidentReportCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=2000)
    category: str
    severity: str
    location_text: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class IncidentReportStatusUpdate(BaseModel):
    status: str


class IncidentReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reporter_id: str
    title: str
    description: str
    category: str
    severity: str
    location_text: Optional[str] = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
