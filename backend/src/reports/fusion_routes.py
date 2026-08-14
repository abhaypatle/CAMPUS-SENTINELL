from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.auth.deps import get_current_user, require_role
from src.models.user import User, UserRole
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.reports.fusion_schemas import FusedIncidentCreate, FusedIncidentOut
from src.reports.fusion_service import run_fusion
from src.ai.mock_provider import MockFusionProvider

router = APIRouter()


@router.post("/api/v1/fusions", response_model=FusedIncidentOut, status_code=status.HTTP_201_CREATED)
def create_fusion(payload: FusedIncidentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RESPONDER.value, UserRole.ADMIN.value))):
    try:
        fused = run_fusion(payload.report_ids, db, MockFusionProvider(), created_by=current_user.id)
    except ValueError as e:
        msg = str(e)
        if msg == "at least two unique report IDs required":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
        if msg == "one or more report IDs not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if msg == "duplicate fused incident":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # build output
    associated = db.query(FusedIncidentReport).filter(FusedIncidentReport.fused_incident_id == fused.id).all()
    report_ids = [a.report_id for a in associated]
    out = FusedIncidentOut(
        id=fused.id,
        created_by=fused.created_by,
        provider=fused.provider,
        confidence=fused.confidence,
        reason=fused.reason,
        evidence=fused.evidence,
        report_ids=report_ids,
        created_at=fused.created_at,
    )
    return out


@router.get("/api/v1/fusions/{fusion_id}", response_model=FusedIncidentOut)
def get_fusion(fusion_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fused = db.query(FusedIncident).filter(FusedIncident.id == fusion_id).first()
    if not fused:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fusion not found")

    # visibility: reporter may view only if they own at least one linked report
    if current_user.role == UserRole.REPORTER.value:
        # check ownership: join to IncidentReport by report_id
        from src.models.incident import IncidentReport

        assoc = (
            db.query(FusedIncidentReport)
            .join(IncidentReport, FusedIncidentReport.report_id == IncidentReport.id)
            .filter(FusedIncidentReport.fused_incident_id == fusion_id, IncidentReport.reporter_id == current_user.id)
            .first()
        )
        if not assoc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this fusion")

    associated = db.query(FusedIncidentReport).filter(FusedIncidentReport.fused_incident_id == fused.id).all()
    report_ids = [a.report_id for a in associated]
    out = FusedIncidentOut(
        id=fused.id,
        created_by=fused.created_by,
        provider=fused.provider,
        confidence=fused.confidence,
        reason=fused.reason,
        evidence=fused.evidence,
        report_ids=report_ids,
        created_at=fused.created_at,
    )
    return out


@router.get("/api/v1/reports/{report_id}/fusions", response_model=list[FusedIncidentOut])
def list_fusions_for_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # fetch fused incident ids
    assoc_rows = db.query(FusedIncidentReport).filter(FusedIncidentReport.report_id == report_id).all()
    fused_ids = [a.fused_incident_id for a in assoc_rows]
    fusions = db.query(FusedIncident).filter(FusedIncident.id.in_(fused_ids)).all()

    results = []
    for fused in fusions:
        associated = db.query(FusedIncidentReport).filter(FusedIncidentReport.fused_incident_id == fused.id).all()
        report_ids = [a.report_id for a in associated]
        results.append(
            FusedIncidentOut(
                id=fused.id,
                created_by=fused.created_by,
                provider=fused.provider,
                confidence=fused.confidence,
                reason=fused.reason,
                evidence=fused.evidence,
                report_ids=report_ids,
                created_at=fused.created_at,
            )
        )

    # enforce reporter visibility: filter out those where reporter doesn't own any linked report
    if current_user.role == UserRole.REPORTER.value:
        filtered = []
        from src.models.incident import IncidentReport

        for item in results:
            linked = (
                db.query(IncidentReport)
                .join(FusedIncidentReport, FusedIncidentReport.report_id == IncidentReport.id)
                .filter(FusedIncidentReport.fused_incident_id == item.id, IncidentReport.reporter_id == current_user.id)
                .first()
            )
            if linked:
                filtered.append(item)
        return filtered

    return results
