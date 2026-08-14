from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.auth.deps import get_current_user, require_role
from src.models.user import User, UserRole
from src.reports.escalation_service import evaluate_and_create
from src.models.escalation import EscalationEvent

router = APIRouter()


@router.post("/api/v1/escalations/trigger", status_code=status.HTTP_200_OK)
def trigger_escalation(incident_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    try:
        ev = evaluate_and_create(incident_id, db, created_by=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not ev:
        return {"created": False, "message": "no escalation conditions met"}

    return {"created": True, "id": ev.id, "triggered_rule": ev.triggered_rule}


@router.get("/api/v1/escalations/{escalation_id}")
def get_escalation(escalation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ev = db.query(EscalationEvent).filter(EscalationEvent.id == escalation_id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="escalation not found")

    if current_user.role == UserRole.REPORTER.value:
        from src.models.incident import IncidentReport

        inc = db.query(IncidentReport).filter(IncidentReport.id == ev.incident_id, IncidentReport.reporter_id == current_user.id).first()
        if not inc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return {
        "id": ev.id,
        "incident_id": ev.incident_id,
        "triggered_rule": ev.triggered_rule,
        "trigger_values": ev.trigger_values,
        "evidence": ev.evidence,
        "status": ev.status,
        "created_at": ev.created_at,
    }


@router.get("/api/v1/incidents/{incident_id}/escalations")
def list_incident_escalations(incident_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.REPORTER.value:
        from src.models.incident import IncidentReport

        inc = db.query(IncidentReport).filter(IncidentReport.id == incident_id, IncidentReport.reporter_id == current_user.id).first()
        if not inc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    rows = db.query(EscalationEvent).filter(EscalationEvent.incident_id == incident_id).order_by(EscalationEvent.created_at.desc()).all()
    res = []
    for ev in rows:
        res.append({
            "id": ev.id,
            "triggered_rule": ev.triggered_rule,
            "status": ev.status,
            "created_at": ev.created_at,
        })
    return res


@router.post("/api/v1/escalations/{escalation_id}/acknowledge")
def acknowledge(escalation_id: str, note: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    ev = db.query(EscalationEvent).filter(EscalationEvent.id == escalation_id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="escalation not found")

    ev.status = "ACKNOWLEDGED"
    ev.acknowledged_by = current_user.id
    ev.acknowledged_at = datetime.now(timezone.utc)
    if note:
        ev.resolution_note = (ev.resolution_note or "") + "\n" + note
    db.add(ev)
    db.commit()
    return {"ok": True}


@router.post("/api/v1/escalations/{escalation_id}/action")
def action(escalation_id: str, note: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    ev = db.query(EscalationEvent).filter(EscalationEvent.id == escalation_id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="escalation not found")

    ev.status = "ACTIONED"
    ev.actioned_by = current_user.id
    ev.actioned_at = datetime.now(timezone.utc)
    if note:
        ev.resolution_note = (ev.resolution_note or "") + "\n" + note
    db.add(ev)
    db.commit()
    return {"ok": True}


@router.post("/api/v1/escalations/{escalation_id}/dismiss")
def dismiss(escalation_id: str, note: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    ev = db.query(EscalationEvent).filter(EscalationEvent.id == escalation_id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="escalation not found")

    ev.status = "DISMISSED"
    ev.actioned_by = current_user.id
    ev.actioned_at = datetime.now(timezone.utc)
    if note:
        ev.resolution_note = (ev.resolution_note or "") + "\n" + note
    db.add(ev)
    db.commit()
    return {"ok": True}
