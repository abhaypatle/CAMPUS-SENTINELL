import json
from typing import List
from sqlalchemy.orm import Session

from src.models.incident import IncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.models.risk_assessment import RiskAssessment
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.models.escalation import EscalationEvent
from src.models.recommendation import Recommendation
from src.ai.mock_provider import MockProvider


RAW_MAX = 1024


def _sanitize_raw(raw) -> str:
    # Allow-list keys and redact obvious sensitive tokens
    def redact_string(s: str) -> str:
        import re
        # redact emails
        s = re.sub(r"[\w\.-]+@[\w\.-]+", "[REDACTED_EMAIL]", s)
        # redact bearer tokens
        s = re.sub(r"(?i)bearer\s+[A-Za-z0-9\-\._~\+/]+=*", "[REDACTED_TOKEN]", s)
        # redact api keys patterns (simple heuristic)
        s = re.sub(r"api[_-]?key[\"']?[:=\s]*[A-Za-z0-9\-\._]{8,}", "[REDACTED_API_KEY]", s, flags=re.IGNORECASE)
        # redact long alphanumeric tokens (heuristic >40 chars)
        s = re.sub(r"[A-Za-z0-9\-_]{40,}", "[REDACTED_TOKEN]", s)
        # redact phone-like patterns
        s = re.sub(r"\+?\d[\d \-\(\)]{7,}\d", "[REDACTED_PHONE]", s)
        return s

    try:
        if isinstance(raw, dict):
            allowed = {}
            for k in ("recommended_action", "summary", "provider", "created_at", "reason", "risk_score"):
                if k in raw:
                    v = raw[k]
                    if isinstance(v, str):
                        v = redact_string(v)
                    allowed[k] = v
            s = json.dumps(allowed)
        else:
            s = redact_string(str(raw))
    except Exception:
        s = ""

    if len(s) > RAW_MAX:
        return s[:RAW_MAX] + "..."
    return s


def _gather_anchors(db: Session, incident_id: str):
    anchors = []
    # risk
    risk = db.query(RiskAssessment).filter(RiskAssessment.incident_id == incident_id).order_by(RiskAssessment.created_at.desc()).first()
    if risk:
        anchors.append({"source_type": "risk_assessment", "source_id": risk.id, "excerpt": risk.risk_factors, "score": risk.risk_score})

    # fused
    fused_ids = db.query(FusedIncidentReport.fused_incident_id).filter(FusedIncidentReport.report_id == incident_id).all()
    for fid_tuple in fused_ids:
        fid = fid_tuple[0]
        f = db.query(FusedIncident).filter(FusedIncident.id == fid).first()
        if f:
            anchors.append({"source_type": "fused_incident", "source_id": f.id, "excerpt": f.reason, "score": f.confidence})

    # escalations
    esc = db.query(EscalationEvent).filter(EscalationEvent.incident_id == incident_id).order_by(EscalationEvent.created_at.desc()).first()
    if esc:
        anchors.append({"source_type": "escalation", "source_id": esc.id, "excerpt": esc.triggered_rule, "score": None})

    return anchors


def generate_recommendation(db: Session, incident_id: str, created_by: str | None = None, force_recompute: bool = False) -> Recommendation:
    incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
    if not incident:
        raise ValueError("incident not found")

    # Prefer provider-based recommendation via IncidentAnalysis (existing provider signals)
    analysis = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == incident_id).first()

    anchors = _gather_anchors(db, incident_id)

    if analysis and not force_recompute:
        # use analysis.recommended_action as provider output
        rec_text = analysis.recommended_action[:2000]
        provider = analysis.provider or "analysis"
        provider_raw = _sanitize_raw({"recommended_action": analysis.recommended_action})
        rec = Recommendation(
            incident_id=incident_id,
            provider=provider,
            provider_version=None,
            calculation_version="v1",
            recommendation_text=rec_text,
            recommendation_type="SOP-SUGGESTION",
            confidence=None,
            provider_response_raw=provider_raw,
            evidence_anchors=json.dumps(anchors),
            is_fallback=False,
            created_by=created_by,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    # No provider analysis: deterministic fallback advisory (advisory wording only)
    latest_risk = db.query(RiskAssessment).filter(RiskAssessment.incident_id == incident_id).order_by(RiskAssessment.created_at.desc()).first()
    risk_score = latest_risk.risk_score if latest_risk else None

    # Determine advisory text (do NOT order actions; advisory phrasing)
    if risk_score is not None and risk_score >= 85:
        rec_text = "High operational risk detected. Review evacuation SOP and consider evacuation procedures according to campus protocol. This is advisory only."
        rec_type = "SOP-REVIEW"
    elif risk_score is not None and risk_score >= 70:
        rec_text = "Elevated risk detected. Recommend dispatching response team and reviewing on-site procedures as per SOPs. Advisory only."
        rec_type = "SOP-REVIEW"
    else:
        rec_text = "Monitor the incident and collect additional evidence; review relevant SOPs if situation changes. Advisory only."
        rec_type = "MONITOR"

    provider = "fallback"
    provider_raw = _sanitize_raw({"reason": "deterministic-fallback", "risk_score": risk_score})

    rec = Recommendation(
        incident_id=incident_id,
        provider=provider,
        provider_version=None,
        calculation_version="v1",
        recommendation_text=rec_text,
        recommendation_type=rec_type,
        confidence=None,
        provider_response_raw=provider_raw,
        evidence_anchors=json.dumps(anchors),
        is_fallback=True,
        created_by=created_by,
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def list_recommendations_for_incident(db: Session, incident_id: str, limit: int = 25, offset: int = 0):
    q = db.query(Recommendation).filter(Recommendation.incident_id == incident_id).order_by(Recommendation.created_at.desc()).limit(limit).offset(offset)
    return q.all()


def get_recommendation(db: Session, rec_id: str):
    return db.query(Recommendation).filter(Recommendation.id == rec_id).first()
