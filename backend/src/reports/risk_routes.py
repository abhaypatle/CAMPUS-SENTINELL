from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.auth.deps import get_current_user, require_role
from src.models.user import User, UserRole
from src.reports.risk_schemas import RiskAssessmentCreate, RiskAssessmentOut, RiskFactor
from src.reports.risk_service import create_risk_assessment
from src.models.risk_assessment import RiskAssessment

router = APIRouter()


@router.post("/api/v1/risk/assess", response_model=RiskAssessmentOut, status_code=status.HTTP_201_CREATED)
def assess(payload: RiskAssessmentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    # validate incident exists will be done in service
    try:
        ra = create_risk_assessment(payload.incident_id, db, created_by=current_user.id, calculation_version=payload.calculation_version or "v1")
    except ValueError as e:
        msg = str(e)
        if msg == "incident not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # load risk_factors and convert dicts to RiskFactor models to avoid serializer warnings
    rf_list = []
    try:
        if ra.risk_factors:
            raw = __import__("json").loads(ra.risk_factors)
            for d in raw:
                try:
                    rf = RiskFactor(**d)
                    rf_list.append(rf)
                except Exception:
                    # skip malformed factor
                    continue
    except Exception:
        rf_list = []

    out = RiskAssessmentOut(
        id=ra.id,
        incident_id=ra.incident_id,
        risk_score=ra.risk_score,
        risk_level=ra.risk_level,
        risk_factors=rf_list,
        calculation_version=ra.calculation_version,
        created_at=ra.created_at,
        updated_at=ra.updated_at,
    )

    return out


@router.get("/api/v1/risk/{assessment_id}", response_model=RiskAssessmentOut)
def get_assessment(assessment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ra = db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()
    if not ra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="risk assessment not found")

    # REPORTER may view only if they own the incident
    if current_user.role == UserRole.REPORTER.value:
        from src.models.incident import IncidentReport

        incident = db.query(IncidentReport).filter(IncidentReport.id == ra.incident_id, IncidentReport.reporter_id == current_user.id).first()
        if not incident:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this assessment")

    rf_list = []
    try:
        if ra.risk_factors:
            raw = __import__("json").loads(ra.risk_factors)
            for d in raw:
                try:
                    rf = RiskFactor(**d)
                    rf_list.append(rf)
                except Exception:
                    continue
    except Exception:
        rf_list = []

    out = RiskAssessmentOut(
        id=ra.id,
        incident_id=ra.incident_id,
        risk_score=ra.risk_score,
        risk_level=ra.risk_level,
        risk_factors=rf_list,
        calculation_version=ra.calculation_version,
        created_at=ra.created_at,
        updated_at=ra.updated_at,
    )
    return out


@router.get("/api/v1/incidents/{incident_id}/risk", response_model=list[RiskAssessmentOut])
def list_for_incident(incident_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # REPORTER limited to own incident
    if current_user.role == UserRole.REPORTER.value:
        from src.models.incident import IncidentReport

        incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id, IncidentReport.reporter_id == current_user.id).first()
        if not incident:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view assessments for this incident")

    rows = db.query(RiskAssessment).filter(RiskAssessment.incident_id == incident_id).all()
    out = []
    for ra in rows:
        rf_list = []
        try:
            if ra.risk_factors:
                raw = __import__("json").loads(ra.risk_factors)
                for d in raw:
                    try:
                        rf = RiskFactor(**d)
                        rf_list.append(rf)
                    except Exception:
                        continue
        except Exception:
            rf_list = []

        out.append(RiskAssessmentOut(
            id=ra.id,
            incident_id=ra.incident_id,
            risk_score=ra.risk_score,
            risk_level=ra.risk_level,
            risk_factors=rf_list,
            calculation_version=ra.calculation_version,
            created_at=ra.created_at,
            updated_at=ra.updated_at,
        ))

    return out
