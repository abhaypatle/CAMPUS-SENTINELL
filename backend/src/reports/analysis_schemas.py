from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class IncidentAnalysisCreate(BaseModel):
    summary: str = Field(min_length=1)
    assessed_category: str
    assessed_severity: str
    risk_indicators: Any
    recommended_action: str
    provider: str
    created_at: Optional[datetime] = None


class IncidentAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    summary: str
    assessed_category: str
    assessed_severity: str
    risk_indicators: Any
    recommended_action: str
    provider: str
    created_at: datetime | None = None
