from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.assignment import IncidentAssignment
from src.models.incident import IncidentReport, IncidentStatus
from src.models.user import User, UserRole


def create_assignment(
    db: Session,
    incident_id: str,
    responder_id: str,
    assigned_by: User,
) -> IncidentAssignment:

    incident = db.query(IncidentReport).filter(
        IncidentReport.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    responder = db.query(User).filter(User.id == responder_id).first()

    if not responder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responder not found",
        )

    if responder.role not in (
        UserRole.RESPONDER.value,
        UserRole.ADMIN.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a responder",
        )

    assignment = IncidentAssignment(
        incident_id=incident_id,
        responder_id=responder_id,
        assigned_by=assigned_by.id,
        status="ASSIGNED",
    )

    incident.status = IncidentStatus.IN_PROGRESS.value

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def update_assignment(
    db: Session,
    assignment_id: str,
    status_value: str,
    resolution_note: str | None,
) -> IncidentAssignment:

    assignment = db.query(IncidentAssignment).filter(
        IncidentAssignment.id == assignment_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    assignment.status = status_value
    assignment.resolution_note = resolution_note

    if status_value == "RESOLVED":
        incident = db.query(IncidentReport).filter(
            IncidentReport.id == assignment.incident_id
        ).first()

        if incident:
            incident.status = IncidentStatus.RESOLVED.value

    db.commit()
    db.refresh(assignment)

    return assignment
