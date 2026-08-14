from datetime import datetime
from typing import Any, List
from pydantic import BaseModel, ConfigDict, Field


class FusedIncidentCreate(BaseModel):
    report_ids: List[str] = Field(min_length=2)
    provider: str | None = None


class FusedIncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: str | None
    provider: str
    confidence: float
    reason: str | None
    evidence: Any | None
    report_ids: List[str]
    created_at: datetime | None = None
