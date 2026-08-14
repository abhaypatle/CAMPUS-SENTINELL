from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.auth.deps import get_current_user, require_role
from src.models.user import User, UserRole
from src.models.incident_analysis import IncidentAnalysis
from src.reports.analysis_schemas import IncidentAnalysisOut
from src.reports.analysis_service import run_analysis
from src.ai.mock_provider import MockProvider

router = APIRouter()


@router.post("/api/v1/reports/{report_id}/analyze", response_model=IncidentAnalysisOut, status_code=status.HTTP_201_CREATED)
def analyze_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    # only RESPONDER and ADMIN may trigger
    try:
        analysis = run_analysis(report_id, db, MockProvider())
    except ValueError as e:
        msg = str(e)
        if msg == "incident not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if msg == "analysis already exists":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return analysis


@router.get("/api/v1/reports/{report_id}/analysis", response_model=IncidentAnalysisOut)
def get_analysis(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == report_id).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis not found")

    # visibility: REPORTER can view if they own the incident; reuse reports access rules
    # Get incident owner by joining; but simplest: compare via relationship-less query
    from src.models.incident import IncidentReport

    incident = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="incident not found")

    if current_user.role == UserRole.REPORTER.value and incident.reporter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this analysis")

    return analysis
