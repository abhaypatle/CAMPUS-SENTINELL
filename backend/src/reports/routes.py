
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.deps import get_current_user
from src.db.session import get_db
from src.models.incident import (
    IncidentCategory,
    IncidentReport,
    IncidentSeverity,
    IncidentStatus,
)
from src.models.user import User, UserRole
from src.reports.schemas import (
    IncidentReportCreate,
    IncidentReportOut,
    IncidentReportStatusUpdate,
)


router = APIRouter()


@router.post(
    "/api/v1/reports",
    response_model=IncidentReportOut,
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    payload: IncidentReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate category.
    try:
        IncidentCategory(payload.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid category",
        )

    # Validate severity.
    try:
        IncidentSeverity(payload.severity)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid severity",
        )

    report = IncidentReport(
        reporter_id=current_user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        severity=payload.severity,
        location_text=payload.location_text,
        status=IncidentStatus.OPEN.value,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


@router.get(
    "/api/v1/reports",
    response_model=list[IncidentReportOut],
)
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Reporters can only see their own reports.
    if current_user.role == UserRole.REPORTER.value:
        reports = (
            db.query(IncidentReport)
            .filter(
                IncidentReport.reporter_id == current_user.id
            )
            .order_by(IncidentReport.created_at.desc())
            .all()
        )

    # Responders and admins can see all reports.
    else:
        reports = (
            db.query(IncidentReport)
            .order_by(IncidentReport.created_at.desc())
            .all()
        )

    return reports


@router.get(
    "/api/v1/reports/{report_id}",
    response_model=IncidentReportOut,
)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(IncidentReport)
        .filter(IncidentReport.id == report_id)
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # Reporters can only access their own reports.
    if (
        current_user.role == UserRole.REPORTER.value
        and report.reporter_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )

    return report


@router.patch(
    "/api/v1/reports/{report_id}/status",
    response_model=IncidentReportOut,
)
def update_report_status(
    report_id: str,
    payload: IncidentReportStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only responders and admins can update status.
    if current_user.role not in [
        UserRole.RESPONDER.value,
        UserRole.ADMIN.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update report status",
        )

    # Validate requested status.
    try:
        new_status = IncidentStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid status",
        )

    report = (
        db.query(IncidentReport)
        .filter(IncidentReport.id == report_id)
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    report.status = new_status.value

    db.commit()
    db.refresh(report)

    return report