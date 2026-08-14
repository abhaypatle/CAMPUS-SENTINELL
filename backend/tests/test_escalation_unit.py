from src.db.session import SessionLocal, Base, engine
from src.models.incident import IncidentReport
from src.models.risk_assessment import RiskAssessment
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.reports.risk_service import create_risk_assessment
from src.reports.escalation_service import evaluate_and_create, evaluate_rules
from datetime import datetime, timedelta


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_immediate_critical_triggers():
    db = SessionLocal()
    try:
        db.query(FusedIncidentReport).delete()
        db.query(FusedIncident).delete()
        db.query(IncidentAnalysis).delete()
        db.query(RiskAssessment).delete()
        db.query(IncidentReport).delete()
        db.commit()

        ir = IncidentReport(reporter_id="u1", title="t", description="d", category="FIRE", severity="CRITICAL")
        db.add(ir)
        db.commit()
        db.refresh(ir)

        # create risk assessment (v1)
        ra = create_risk_assessment(ir.id, db)

        ev = evaluate_and_create(ir.id, db)
        assert ev is not None
        assert ev.triggered_rule == "ImmediateCritical"
    finally:
        db.close()
