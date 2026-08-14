import json
from src.db.session import SessionLocal, Base, engine
from src.models.incident import IncidentReport
from src.models.risk_assessment import RiskAssessment
from src.reports.risk_service import compute_risk_score, create_risk_assessment


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    pass


def test_compute_base_severity_only():
    db = SessionLocal()
    try:
        db.query(RiskAssessment).delete()
        db.query(IncidentReport).delete()
        db.commit()

        ir = IncidentReport(reporter_id="u1", title="t", description="d", category="OTHER", severity="MEDIUM")
        db.add(ir)
        db.commit()
        db.refresh(ir)

        score, level, factors = compute_risk_score(ir.id, db)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        assert any(f["key"] == "base_severity" for f in factors)
    finally:
        db.close()
