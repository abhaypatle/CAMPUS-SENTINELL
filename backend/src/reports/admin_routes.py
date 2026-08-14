from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.auth.deps import require_role
from src.db.session import get_db
from src.models.user import UserRole
from src.reports.admin_service import list_incidents, get_intelligence, list_escalations, stats
from src.reports.admin_schemas import IncidentBrief, IncidentIntelligence, EscalationBrief, AdminStats

router = APIRouter()


@router.get("/api/v1/admin/incidents", response_model=List[IncidentBrief])
def admin_list_incidents(page: int = 1, per_page: int = 25, db: Session = Depends(get_db), current_user=Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    offset = (page - 1) * per_page
    items = list_incidents(db, limit=per_page, offset=offset)
    return items


@router.get("/api/v1/admin/incidents/{incident_id}/intelligence", response_model=IncidentIntelligence)
def admin_intelligence(incident_id: str, db: Session = Depends(get_db), current_user=Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    data = get_intelligence(db, incident_id)
    # transform to schema-friendly dict
    fused = [
        {"id": f.id, "confidence": f.confidence, "reason": f.reason, "evidence": f.evidence}
        for f in (data.get("fused") or [])
    ]
    escalations = [
        {"id": e.id, "triggered_rule": e.triggered_rule, "status": e.status, "created_at": e.created_at}
        for e in (data.get("escalations") or [])
    ]

    recommendations = []
    for r in (data.get("recommendations") or []):
        recommendations.append({
            "id": r.id,
            "provider": r.provider,
            "recommendation_type": r.recommendation_type,
            "is_fallback": r.is_fallback,
            "created_at": r.created_at,
        })

    return {
        "incident": data["incident"],
        "analysis": data.get("analysis"),
        "risk": data.get("risk"),
        "fused": fused,
        "escalations": escalations,
        "recommendations": recommendations,
    }


@router.get("/api/v1/admin/escalations", response_model=List[EscalationBrief])
def admin_list_escalations(page: int = 1, per_page: int = 25, status: str | None = Query(None), db: Session = Depends(get_db), current_user=Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    offset = (page - 1) * per_page
    filters = {}
    if status:
        filters["status"] = status
    items = list_escalations(db, limit=per_page, offset=offset, filters=filters)
    return items


@router.get("/api/v1/admin/stats", response_model=AdminStats)
def admin_stats(db: Session = Depends(get_db), current_user=Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    s = stats(db)
    return s
