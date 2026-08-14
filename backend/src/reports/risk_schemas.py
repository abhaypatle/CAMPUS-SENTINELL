from datetime import datetime
from typing import Any, List
from pydantic import BaseModel, ConfigDict


class RiskAssessmentCreate(BaseModel):
    incident_id: str
    calculation_version: str | None = "v1"


class RiskFactor(BaseModel):
    key: str
    value: Any
    contribution: float
    explanation: str
    source: str


class RiskAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    risk_score: float
    risk_level: str
    risk_factors: List[RiskFactor]
    calculation_version: str
    created_at: datetime
    updated_at: datetime
