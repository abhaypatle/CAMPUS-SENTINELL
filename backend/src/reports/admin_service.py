from typing import List
from sqlalchemy.orm import Session

from src.models.incident import IncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.models.risk_assessment import RiskAssessment
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.models.escalation import EscalationEvent


def list_incidents(db: Session, limit: int = 25, offset: int = 0, filters: dict | None = None) -> List[IncidentReport]:
    q = db.query(IncidentReport).order_by(IncidentReport.created_at.desc()).limit(limit).offset(offset)
    # apply simple filters
    if filters:
        if "category" in filters:
            q = q.filter(IncidentReport.category == filters["category"])
        if "severity" in filters:
            q = q.filter(IncidentReport.severity == filters["severity"])
    return q.all()


def get_intelligence(db: Session, incident_id: str) -> dict:
    incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()

    analysis = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == incident_id).first()

    risk = db.query(RiskAssessment).filter(RiskAssessment.incident_id == incident_id).order_by(RiskAssessment.created_at.desc()).first()

    # find fused incidents that include this report
    fused_ids = db.query(FusedIncidentReport.fused_incident_id).filter(FusedIncidentReport.report_id == incident_id).all()
    fused_list = []
    for fid_tuple in fused_ids:
        fid = fid_tuple[0]
        f = db.query(FusedIncident).filter(FusedIncident.id == fid).first()
        if f:
            fused_list.append(f)

    escalations = db.query(EscalationEvent).filter(EscalationEvent.incident_id == incident_id).order_by(EscalationEvent.created_at.desc()).all()

    # recommendations (new STEP 14)
    try:
        from src.models.recommendation import Recommendation
        recs = db.query(Recommendation).filter(Recommendation.incident_id == incident_id).order_by(Recommendation.created_at.desc()).all()
    except Exception:
        recs = []

    return {
        "incident": incident,
        "analysis": analysis,
        "risk": risk,
        "fused": fused_list,
        "escalations": escalations,
        "recommendations": recs,
    }


def list_escalations(db: Session, limit: int = 25, offset: int = 0, filters: dict | None = None):
    q = db.query(EscalationEvent).order_by(EscalationEvent.created_at.desc()).limit(limit).offset(offset)
    if filters:
        if "status" in filters:
            q = q.filter(EscalationEvent.status == filters["status"])
    return q.all()


def stats(db: Session) -> dict:
    open_incidents = db.query(IncidentReport).filter(IncidentReport.status == "OPEN").count()
    active_escalations = db.query(EscalationEvent).filter(EscalationEvent.status == "PENDING").count()
    # high risk threshold from STEP11: treat >=70 as high (v1)
    high_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_score >= 70.0).count()
    return {
        "open_incidents": open_incidents,
        "active_escalations": active_escalations,
        "high_risk_count": high_risk,
    }
