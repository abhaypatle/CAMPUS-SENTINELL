import sys
import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

# Ensure backend package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.db.session import engine, SessionLocal, Base
from src.models.user import User
from src.models.incident import IncidentReport
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.reports.fusion_service import run_fusion

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(FusedIncidentReport).delete()
        db.query(FusedIncident).delete()
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


valid_payload = {
    "title": "Test Incident",
    "description": "Something happened",
    "category": "SAFETY",
    "severity": "LOW",
    "location_text": "Building A",
}


def _mk_report(email_base="r"):
    email = f"{email_base}@example.com"
    register_user(name=email_base, email=email)
    token = login_user(email=email).json().get("access_token")
    resp = create_report(token, valid_payload)
    assert resp.status_code == 201
    return resp.json(), token


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


def test_duplicate_fusion_returns_409_and_one_exists():
    r1, _ = _mk_report("r1")
    r2, _ = _mk_report("r2")

    token = _make_admin_or_resp("resp@example.com", "RESPONDER")

    # create fusion [r1, r2]
    resp = client.post("/api/v1/fusions", json={"report_ids": [r1["id"], r2["id"]]}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()

    # attempt reversed order should 409
    resp2 = client.post("/api/v1/fusions", json={"report_ids": [r2["id"], r1["id"]]}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 409

    db = SessionLocal()
    try:
        count = db.query(FusedIncident).count()
        assert count == 1
    finally:
        db.close()


def test_provider_output_validation_rejects_and_no_persistence():
    # make two reports
    r1, _ = _mk_report("pv1")
    r2, _ = _mk_report("pv2")

    db = SessionLocal()
    try:
        # define invalid provider
        class BadProvider:
            def analyze(self, reports):
                return {"provider": "bad-provider", "confidence": "not-a-float"}

        # call run_fusion directly
        with pytest.raises(ValueError):
            run_fusion([r1["id"], r2["id"]], db, BadProvider(), created_by=None)

        # ensure no fused rows
        assert db.query(FusedIncident).count() == 0
        assert db.query(FusedIncidentReport).count() == 0
    finally:
        db.close()


def test_reporter_visibility_and_access_controls():
    # Reporter A
    r1, token_a = _mk_report("ra")
    # Reporter B
    r2, token_b = _mk_report("rb")

    # responder creates fusion
    token_resp = _make_admin_or_resp("resp2@example.com", "RESPONDER")
    resp = client.post("/api/v1/fusions", json={"report_ids": [r1["id"], r2["id"]]}, headers={"Authorization": f"Bearer {token_resp}"})
    assert resp.status_code == 201
    fusion = resp.json()

    # Reporter A can GET
    resp_a = client.get(f"/api/v1/fusions/{fusion['id']}", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a.status_code == 200

    # Reporter B can GET
    resp_b = client.get(f"/api/v1/fusions/{fusion['id']}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 200

    # Reporter C (owns neither) should get 403
    # Create reporter C directly to avoid intermittent testclient registration issues
    from src.auth.hash import hash_password
    db = SessionLocal()
    try:
        u = User(name="C", email="c@example.com", password_hash=hash_password("password123"))
        db.add(u)
        db.commit()
    finally:
        db.close()
    login_resp_c = login_user(email="c@example.com")
    assert login_resp_c.status_code == 200
    token_c = login_resp_c.json().get("access_token")
    resp_c = client.get(f"/api/v1/fusions/{fusion['id']}", headers={"Authorization": f"Bearer {token_c}"})
    assert resp_c.status_code == 403


def test_reporter_cannot_create_but_responder_and_admin_can():
    r1, _ = _mk_report("cr1")
    r2, _ = _mk_report("cr2")

    # reporter try create
    register_user(name="RepX", email="repx2@example.com")
    token_rep = login_user(email="repx2@example.com").json().get("access_token")
    resp = client.post("/api/v1/fusions", json={"report_ids": [r1["id"], r2["id"]]}, headers={"Authorization": f"Bearer {token_rep}"})
    assert resp.status_code == 403

    # responder can create
    token_resp = _make_admin_or_resp("resp3@example.com", "RESPONDER")
    resp2 = client.post("/api/v1/fusions", json={"report_ids": [r1["id"], r2["id"]]}, headers={"Authorization": f"Bearer {token_resp}"})
    assert resp2.status_code == 201

    # admin can create (create new reports)
    r3, _ = _mk_report("cr3")
    r4, _ = _mk_report("cr4")
    token_admin = _make_admin_or_resp("admin2@example.com", "ADMIN")
    resp3 = client.post("/api/v1/fusions", json={"report_ids": [r3["id"], r4["id"]]}, headers={"Authorization": f"Bearer {token_admin}"})
    assert resp3.status_code == 201


def test_minimum_reports_and_duplicate_ids_rejected():
    r1, _ = _mk_report("min1")

    token = _make_admin_or_resp("resp4@example.com", "RESPONDER")

    # single report
    resp = client.post("/api/v1/fusions", json={"report_ids": [r1["id"]]}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422

    # duplicate ids
    resp2 = client.post("/api/v1/fusions", json={"report_ids": [r1["id"], r1["id"]]}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 422


def test_invalid_report_id_returns_404_and_no_partial_persistence():
    r1, _ = _mk_report("inv1")
    token = _make_admin_or_resp("resp5@example.com", "RESPONDER")

    resp = client.post("/api/v1/fusions", json={"report_ids": [r1["id"], "no-such-id"]}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404

    db = SessionLocal()
    try:
        assert db.query(FusedIncident).count() == 0
        assert db.query(FusedIncidentReport).count() == 0
    finally:
        db.close()


def test_original_reports_preserved_and_association_integrity_and_confidence():
    # create two reports with known fields
    payload = dict(valid_payload)
    payload["title"] = "Preserve Title"
    payload["description"] = "Preserve Desc"

    register_user(name="P1", email="p1@example.com")
    token1 = login_user(email="p1@example.com").json().get("access_token")
    r1 = create_report(token1, payload).json()

    register_user(name="P2", email="p2@example.com")
    token2 = login_user(email="p2@example.com").json().get("access_token")
    r2 = create_report(token2, payload).json()

    token_resp = _make_admin_or_resp("resp6@example.com", "RESPONDER")
    resp = client.post("/api/v1/fusions", json={"report_ids": [r1["id"], r2["id"]]}, headers={"Authorization": f"Bearer {token_resp}"})
    assert resp.status_code == 201
    fusion = resp.json()

    db = SessionLocal()
    try:
        # original reports still exist and fields preserved
        orig1 = db.query(IncidentReport).filter(IncidentReport.id == r1["id"]).first()
        orig2 = db.query(IncidentReport).filter(IncidentReport.id == r2["id"]).first()
        assert orig1 is not None and orig2 is not None
        assert orig1.title == payload["title"]
        assert orig1.description == payload["description"]

        # association integrity: each report linked once
        assoc_count_r1 = db.query(FusedIncidentReport).filter(FusedIncidentReport.report_id == r1["id"], FusedIncidentReport.fused_incident_id == fusion["id"]).count()
        assert assoc_count_r1 == 1

        # confidence bounds
        fused_db = db.query(FusedIncident).filter(FusedIncident.id == fusion["id"]).first()
        assert fused_db is not None
        assert 0.0 <= fused_db.confidence <= 1.0

    finally:
        db.close()
