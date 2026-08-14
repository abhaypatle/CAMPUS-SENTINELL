import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from pydantic import ValidationError
from src.models.incident import IncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.reports.analysis_schemas import IncidentAnalysisCreate
from src.ai.base import AIProvider


def run_analysis(incident_id: str, db: Session, provider: AIProvider) -> IncidentAnalysis:
    incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
    if not incident:
        raise ValueError("incident not found")

    # ensure no existing analysis (single-analysis-per-incident)
    existing = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == incident_id).first()
    if existing:
        raise ValueError("analysis already exists")

    result = provider.analyze(incident)

    try:
        validated = IncidentAnalysisCreate(**result)
    except ValidationError as e:
        raise ValueError(f"invalid provider output: {e}")

    # normalize risk_indicators to JSON string for storage
    ri = validated.risk_indicators
    if not isinstance(ri, str):
        ri = json.dumps(ri)

    analysis_kwargs = dict(
        incident_id=incident_id,
        summary=validated.summary,
        assessed_category=validated.assessed_category,
        assessed_severity=validated.assessed_severity,
        risk_indicators=ri,
        recommended_action=validated.recommended_action,
        provider=validated.provider,
    )

    # Persist created_at if provider supplied it; otherwise allow SQLAlchemy default
    if getattr(validated, "created_at", None) is not None:
        analysis_kwargs["created_at"] = validated.created_at

    analysis = IncidentAnalysis(**analysis_kwargs)

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis
