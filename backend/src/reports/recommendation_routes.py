from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from src.auth.deps import get_current_user, require_role
from src.db.session import get_db
from src.models.user import UserRole
from src.reports.recommendation_service import generate_recommendation, list_recommendations_for_incident, get_recommendation
from src.reports.recommendation_schemas import RecommendationOut

router = APIRouter()


@router.post("/api/v1/recommendations/generate", response_model=RecommendationOut)
def post_generate(incident_id: str, db: Session = Depends(get_db), current_user = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    try:
        rec = generate_recommendation(db, incident_id, created_by=current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="incident not found")

    anchors = []
    try:
        anchors = json.loads(rec.evidence_anchors) if rec.evidence_anchors else []
    except Exception:
        anchors = []

    return {
        "id": rec.id,
        "incident_id": rec.incident_id,
        "provider": rec.provider,
        "provider_version": rec.provider_version,
        "calculation_version": rec.calculation_version,
        "recommendation_text": rec.recommendation_text,
        "recommendation_type": rec.recommendation_type,
        "confidence": None,
        "is_fallback": rec.is_fallback,
        "evidence_anchors": anchors,
        "created_by": rec.created_by,
        "created_at": rec.created_at,
    }


@router.get("/api/v1/incidents/{incident_id}/recommendations", response_model=list[RecommendationOut])
def get_incident_recs(incident_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # reporters may only view their own incident's recommendations
    if current_user.role == 'REPORTER':
        # check ownership
        from src.models.incident import IncidentReport
        ir = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
        if not ir:
            raise HTTPException(status_code=404, detail="incident not found")
        if ir.reporter_id != current_user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")

    items = list_recommendations_for_incident(db, incident_id)
    out = []
    for rec in items:
        try:
            anchors = json.loads(rec.evidence_anchors) if rec.evidence_anchors else []
        except Exception:
            anchors = []
        out.append({
            "id": rec.id,
            "incident_id": rec.incident_id,
            "provider": rec.provider,
            "provider_version": rec.provider_version,
            "calculation_version": rec.calculation_version,
            "recommendation_text": rec.recommendation_text,
            "recommendation_type": rec.recommendation_type,
            "confidence": None,
            "is_fallback": rec.is_fallback,
            "evidence_anchors": anchors,
            "created_by": rec.created_by,
            "created_at": rec.created_at,
        })
    return out


@router.get("/api/v1/recommendations/{rec_id}", response_model=RecommendationOut)
def get_rec(rec_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    rec = get_recommendation(db, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")

    # if reporter, ensure they own the incident
    if current_user.role == 'REPORTER':
        from src.models.incident import IncidentReport
        ir = db.query(IncidentReport).filter(IncidentReport.id == rec.incident_id).first()
        if not ir or ir.reporter_id != current_user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")

    try:
        anchors = json.loads(rec.evidence_anchors) if rec.evidence_anchors else []
    except Exception:
        anchors = []

    return {
        "id": rec.id,
        "incident_id": rec.incident_id,
        "provider": rec.provider,
        "provider_version": rec.provider_version,
        "calculation_version": rec.calculation_version,
        "recommendation_text": rec.recommendation_text,
        "recommendation_type": rec.recommendation_type,
        "confidence": None,
        "is_fallback": rec.is_fallback,
        "evidence_anchors": anchors,
        "created_by": rec.created_by,
        "created_at": rec.created_at,
    }
