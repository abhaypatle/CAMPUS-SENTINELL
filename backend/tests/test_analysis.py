import sys
import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.db.session import engine, SessionLocal, Base
from src.models.user import User
from src.models.incident import IncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.reports.analysis_service import run_analysis

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(IncidentAnalysis).delete()
        db.query(IncidentReport).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    yield


def register_user(name="U", email="u@example.com", password="password123"):
    return client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": password})


def login_user(email="u@example.com", password="password123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def create_report(token, payload):
    headers = {"Authorization": f"Bearer {token}"}
    return client.post("/api/v1/reports", json=payload, headers=headers)


def analyze(token, report_id):
    headers = {"Authorization": f"Bearer {token}"}
    return client.post(f"/api/v1/reports/{report_id}/analyze", headers=headers)


def get_analysis(token, report_id):
    headers = {"Authorization": f"Bearer {token}"}
    return client.get(f"/api/v1/reports/{report_id}/analysis", headers=headers)


valid_payload = {
    "title": "Test Incident",
    "description": "Smoke in hallway",
    "category": "SAFETY",
    "severity": "LOW",
    "location_text": "B1",
}


def test_responder_and_admin_can_trigger_analysis_and_persistence():
    # reporter creates report
    register_user(name="rep", email="rep@example.com")
    token_rep = login_user(email="rep@example.com").json().get("access_token")
    resp = create_report(token_rep, valid_payload)
    assert resp.status_code == 201
    report_id = resp.json().get("id")

    # create responder and promote role
    register_user(name="resp", email="resp@example.com")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "resp@example.com").first()
        user.role = "RESPONDER"
        db.add(user)
        db.commit()
    finally:
        db.close()

    token_resp = login_user(email="resp@example.com").json().get("access_token")
    r = analyze(token_resp, report_id)
    assert r.status_code == 201
    data = r.json()
    assert data["incident_id"] == report_id

    # admin can also trigger (create new report and analyze)
    register_user(name="admin", email="admin@example.com")
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        admin.role = "ADMIN"
        db.add(admin)
        db.commit()
    finally:
        db.close()

    token_admin = login_user(email="admin@example.com").json().get("access_token")
    # create another report
    resp2 = create_report(token_rep, dict(valid_payload, title="Second"))
    report2_id = resp2.json().get("id")
    r2 = analyze(token_admin, report2_id)
    assert r2.status_code == 201


def test_reporter_cannot_trigger_analysis_and_get_access_control():
    reg_resp = register_user(name="reporterA", email="r@example.com")
    assert reg_resp.status_code == 201
    login_resp = login_user(email="r@example.com")
    assert login_resp.status_code == 200
    token_r = login_resp.json().get("access_token")
    resp = create_report(token_r, valid_payload)
    assert resp.status_code == 201
    report_id = resp.json().get("id")

    # reporter attempting to trigger analysis should get 403
    resp = analyze(token_r, report_id)
    assert resp.status_code == 403

    # But reporter can GET their own analysis after responder created it
    # create responder and run analysis
    register_user(name="resp2", email="resp2@example.com")
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "resp2@example.com").first()
        u.role = "RESPONDER"
        db.add(u)
        db.commit()
    finally:
        db.close()
    token_resp2 = login_user(email="resp2@example.com").json().get("access_token")
    analyze(token_resp2, report_id)

    # reporter should be able to GET analysis
    g = get_analysis(token_r, report_id)
    assert g.status_code == 200


def test_duplicate_analysis_behaviour():
    register_user(name="repx", email="repx@example.com")
    token_rep = login_user(email="repx@example.com").json().get("access_token")
    resp = create_report(token_rep, valid_payload)
    report_id = resp.json().get("id")

    # make responder
    register_user(name="resp3", email="resp3@example.com")
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "resp3@example.com").first()
        u.role = "RESPONDER"
        db.add(u)
        db.commit()
    finally:
        db.close()
    token_resp3 = login_user(email="resp3@example.com").json().get("access_token")

    r1 = analyze(token_resp3, report_id)
    assert r1.status_code == 201
    r2 = analyze(token_resp3, report_id)
    assert r2.status_code == 409


def test_invalid_provider_output_rejection():
    # use run_analysis directly with a bad provider to exercise validation
    register_user(name="rep4", email="rep4@example.com")
    token = login_user(email="rep4@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    report_id = resp.json().get("id")

    class BadProvider:
        def analyze(self, incident):
            return {"bad": "data"}

    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            run_analysis(report_id, db, BadProvider())
        # ensure no analysis row created
        a = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == report_id).first()
        assert a is None
    finally:
        db.close()


def test_original_incident_category_and_severity_unchanged():
    register_user(name="rep5", email="rep5@example.com")
    token = login_user(email="rep5@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    report_id = resp.json().get("id")

    # run analysis via responder
    register_user(name="resp4", email="resp4@example.com")
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "resp4@example.com").first()
        u.role = "RESPONDER"
        db.add(u)
        db.commit()
    finally:
        db.close()
    token_resp4 = login_user(email="resp4@example.com").json().get("access_token")
    analyze(token_resp4, report_id)

    db = SessionLocal()
    try:
        inc = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
        assert inc.category == "SAFETY"
        assert inc.severity == "LOW"
    finally:
        db.close()


def test_keyword_based_assessment_fire_and_medical_and_critical_and_created_at_persistence():
    # fire/smoke -> FIRE
    register_user(name="repf", email="repf@example.com")
    token = login_user(email="repf@example.com").json().get("access_token")
    payload_fire = dict(valid_payload, title="Fire in kitchen", description="Smoke and flame observed")
    resp = create_report(token, payload_fire)
    report_id = resp.json().get("id")

    # make responder
    register_user(name="respf", email="respf@example.com")
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "respf@example.com").first()
        u.role = "RESPONDER"
        db.add(u)
        db.commit()
    finally:
        db.close()

    token_resp = login_user(email="respf@example.com").json().get("access_token")
    r = analyze(token_resp, report_id)
    assert r.status_code == 201
    data = r.json()
    assert data["assessed_category"] == "FIRE"

    # injury -> MEDICAL
    register_user(name="repm", email="repm@example.com")
    tokenm = login_user(email="repm@example.com").json().get("access_token")
    payload_med = dict(valid_payload, title="Person injured", description="One person unconscious and bleeding")
    resp2 = create_report(tokenm, payload_med)
    report2_id = resp2.json().get("id")

    token_resp2 = token_resp  # reuse responder
    r2 = analyze(token_resp2, report2_id)
    assert r2.status_code == 201
    data2 = r2.json()
    assert data2["assessed_category"] == "MEDICAL"

    # critical keyword -> CRITICAL
    register_user(name="repc", email="repc@example.com")
    tokenc = login_user(email="repc@example.com").json().get("access_token")
    payload_crit = dict(valid_payload, title="Unconscious person", description="Someone unconscious, life-threatening")
    resp3 = create_report(tokenc, payload_crit)
    report3_id = resp3.json().get("id")

    r3 = analyze(token_resp, report3_id)
    assert r3.status_code == 201
    data3 = r3.json()
    assert data3["assessed_severity"] == "CRITICAL"

    # provider created_at should be present and persisted
    assert data3.get("created_at") is not None

    # ensure original incident category/severity unchanged for one of these
    db = SessionLocal()
    try:
        inc = db.query(IncidentReport).filter(IncidentReport.id == report3_id).first()
        assert inc.category == "SAFETY"
        assert inc.severity == "LOW"
    finally:
        db.close()
