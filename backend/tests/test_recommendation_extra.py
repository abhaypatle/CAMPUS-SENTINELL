import sys
import os
import json

from fastapi.testclient import TestClient
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.db.session import engine, SessionLocal, Base
from src.models.user import User
from src.models.incident import IncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.models.recommendation import Recommendation

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Recommendation).delete()
        db.query(IncidentAnalysis).delete()
        db.query(IncidentReport).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    yield


def register_user(name="Reporter", email="rep@example.com", password="password123"):
    return client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": password})


def login_user(email="rep@example.com", password="password123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def create_report(token, payload):
    headers = {"Authorization": f"Bearer {token}"}
    return client.post("/api/v1/reports", json=payload, headers=headers)


def _make_admin_or_resp(email, role):
    register_user(name=email.split("@")[0], email=email)
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        u.role = role
        db.add(u)
        db.commit()
    finally:
        db.close()
    token = login_user(email=email).json().get("access_token")
    return token


valid_payload = {
    "title": "Test Incident",
    "description": "Something happened",
    "category": "SAFETY",
    "severity": "LOW",
    "location_text": "Building A",
}


def test_reporter_cannot_generate():
    register_user(name="Rep", email="rep_block@example.com")
    token = login_user(email="rep_block@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    assert resp.status_code == 201
    incident_id = resp.json().get("id")

    # reporter tries to generate
    r = client.post("/api/v1/recommendations/generate", params={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_truncation_and_redaction_of_provider_raw():
    register_user(name="Rep", email="rep_redact@example.com")
    token = login_user(email="rep_redact@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    incident_id = resp.json().get("id")

    # create analysis with long text containing sensitive info
    long_text = "Contact admin at secret@example.com. Bearer abcdefghijklmnopqrstuvwxyz1234567890. " + ("x" * 2000)
    db = SessionLocal()
    try:
        ia = IncidentAnalysis(
            incident_id=incident_id,
            summary="analysis",
            assessed_category="SAFETY",
            assessed_severity="HIGH",
            risk_indicators="{}",
            recommended_action=long_text,
            provider="mock",
        )
        db.add(ia)
        db.commit()
    finally:
        db.close()

    token_resp = _make_admin_or_resp("resp_redact@example.com", "RESPONDER")
    r = client.post("/api/v1/recommendations/generate", params={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token_resp}"})
    assert r.status_code == 200

    # inspect DB for persisted provider_response_raw
    db = SessionLocal()
    try:
        rec = db.query(Recommendation).filter(Recommendation.incident_id == incident_id).order_by(Recommendation.created_at.desc()).first()
        assert rec is not None
        raw = rec.provider_response_raw or ""
        assert len(raw) <= 1027
        assert "[REDACTED_EMAIL]" in raw
        assert "[REDACTED_TOKEN]" in raw
    finally:
        db.close()


def test_evidence_anchors_and_no_mutation():
    register_user(name="Rep", email="rep_ea@example.com")
    token = login_user(email="rep_ea@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    incident_id = resp.json().get("id")

    # ensure incident fields
    db = SessionLocal()
    try:
        ir_before = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
        before_cat = ir_before.category
        before_sev = ir_before.severity
        before_status = ir_before.status
    finally:
        db.close()

    token_resp = _make_admin_or_resp("resp_ea@example.com", "RESPONDER")
    r = client.post("/api/v1/recommendations/generate", params={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token_resp}"})
    assert r.status_code == 200

    db = SessionLocal()
    try:
        rec = db.query(Recommendation).filter(Recommendation.incident_id == incident_id).first()
        assert rec is not None
        anchors = rec.evidence_anchors or "[]"
        parsed = json.loads(anchors)
        assert isinstance(parsed, list)

        ir_after = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
        assert ir_after.category == before_cat
        assert ir_after.severity == before_sev
        assert ir_after.status == before_status
    finally:
        db.close()
