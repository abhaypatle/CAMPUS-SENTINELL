from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class IncidentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    severity: str
    status: str
    created_at: datetime | None = None


class RiskBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    risk_score: float
    risk_level: str
    calculation_version: str
    created_at: datetime | None = None


class AnalysisBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessed_severity: str
    assessed_category: str
    provider: str
    created_at: datetime | None = None


class FusionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confidence: float
    reason: Optional[str] = None
    evidence: Optional[str] = None


class EscalationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    triggered_rule: str
    status: str
    created_at: datetime | None = None


class IncidentIntelligence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident: IncidentBrief
    analysis: AnalysisBrief | None = None
    risk: RiskBrief | None = None
    fused: List[FusionBrief] | None = None
    escalations: List[EscalationBrief] | None = None
    recommendations: List[dict] | None = None


class AdminStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    open_incidents: int
    active_escalations: int
    high_risk_count: int
