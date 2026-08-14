from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class EvidenceAnchor(BaseModel):
    source_type: str
    source_id: str
    excerpt: str | None = None
    score: float | None = None


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    provider: str
    provider_version: str | None = None
    calculation_version: str
    recommendation_text: str
    recommendation_type: str | None = None
    confidence: float | None = None
    is_fallback: bool
    evidence_anchors: List[EvidenceAnchor] | None = None
    created_by: str | None = None
    created_at: datetime | None = None
