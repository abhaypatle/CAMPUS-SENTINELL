import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.deps import get_current_user
from src.db.session import get_db
from src.models.audit import AuditEvent
from src.models.user import User
from src.reports.audit_schemas import AuditEventCreate, AuditEventOut


router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit"],
)


@router.post("", response_model=AuditEventOut, status_code=201)
def create_audit_event(
    payload: AuditEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = AuditEvent(
        actor_id=current_user.id,
        action=payload.action,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        details=payload.details,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.get("/resource/{resource_type}/{resource_id}", response_model=list[AuditEventOut])
def list_resource_audit(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(AuditEvent)
        .filter(
            AuditEvent.resource_type == resource_type,
            AuditEvent.resource_id == resource_id,
        )
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
