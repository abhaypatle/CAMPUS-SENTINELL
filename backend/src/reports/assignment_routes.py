from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.deps import get_current_user, require_role
from src.db.session import get_db
from src.models.user import User, UserRole
from src.reports.assignment_schemas import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentUpdate,
)
from src.reports.assignment_service import (
    create_assignment,
    update_assignment,
)

router = APIRouter(
    prefix="/api/v1/assignments",
    tags=["assignments"],
)


@router.post(
    "",
    response_model=AssignmentOut,
    dependencies=[Depends(require_role(
        UserRole.RESPONDER.value,
        UserRole.ADMIN.value,
    ))],
)
def assign_incident(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_assignment(
        db=db,
        incident_id=payload.incident_id,
        responder_id=payload.responder_id,
        assigned_by=current_user,
    )


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentOut,
)
def update_assignment_status(
    assignment_id: str,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_assignment(
        db=db,
        assignment_id=assignment_id,
        status_value=payload.status,
        resolution_note=payload.resolution_note,
    )
