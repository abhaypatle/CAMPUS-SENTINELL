import json
import sys
import os

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

# Ensure backend package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.db.session import engine, SessionLocal, Base
from src.models.user import User
from src.models.incident import IncidentReport

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
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


def list_reports(token):
    headers = {"Authorization": f"Bearer {token}"}
    return client.get("/api/v1/reports", headers=headers)


def get_report(token, report_id):
    headers = {"Authorization": f"Bearer {token}"}
    return client.get(f"/api/v1/reports/{report_id}", headers=headers)


valid_payload = {
    "title": "Test Incident",
    "description": "Something happened",
    "category": "SAFETY",
    "severity": "LOW",
    "location_text": "Building A",
}


def test_create_report_with_valid_jwt():
    register_user()
    token = login_user().json().get("access_token")
    resp = create_report(token, valid_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == valid_payload["title"]
    assert data["reporter_id"] is not None


def test_reject_unauthenticated_create():
    resp = client.post("/api/v1/reports", json=valid_payload)
    assert resp.status_code == 401


def test_reporter_becomes_owner():
    register_user(name="Alice", email="alice@example.com")
    token = login_user(email="alice@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    data = resp.json()
    db = SessionLocal()
    try:
        r = db.query(IncidentReport).filter(IncidentReport.id == data["id"]).first()
        assert r is not None
        assert r.reporter_id == data["reporter_id"]
    finally:
        db.close()


def test_reporter_sees_own_reports():
    register_user(name="Bob", email="bob@example.com")
    token = login_user(email="bob@example.com").json().get("access_token")
    create_report(token, valid_payload)
    resp = list_reports(token)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_reporter_cannot_see_another_reporter_report():
    # Create first reporter and report
    register_user(name="R1", email="r1@example.com")
    token1 = login_user(email="r1@example.com").json().get("access_token")
    resp = create_report(token1, valid_payload)
    report_id = resp.json().get("id")

    # Create second reporter
    register_user(name="R2", email="r2@example.com")
    token2 = login_user(email="r2@example.com").json().get("access_token")
    # second reporter should see zero reports
    resp2 = list_reports(token2)
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0
    # trying to get by id should return 403
    resp3 = get_report(token2, report_id)
    assert resp3.status_code == 403


def test_admin_can_see_all_reports():
    # create reporter and a report
    register_user(name="Rep", email="rep2@example.com")
    token_rep = login_user(email="rep2@example.com").json().get("access_token")
    create_report(token_rep, valid_payload)

    # create admin
    register_user(name="Admin", email="admin@example.com")
    # Manually set role to ADMIN in DB
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        admin.role = "ADMIN"
        db.add(admin)
        db.commit()
    finally:
        db.close()

    token_admin = login_user(email="admin@example.com").json().get("access_token")
    resp = list_reports(token_admin)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_responder_can_see_all_reports():
    # create reporter and a report
    register_user(name="RepX", email="repx@example.com")
    token_rep = login_user(email="repx@example.com").json().get("access_token")
    create_report(token_rep, valid_payload)

    # create responder
    register_user(name="Resp", email="resp@example.com")
    # Manually set role to RESPONDER in DB
    db = SessionLocal()
    try:
        resp_user = db.query(User).filter(User.email == "resp@example.com").first()
        resp_user.role = "RESPONDER"
        db.add(resp_user)
        db.commit()
    finally:
        db.close()

    token_resp = login_user(email="resp@example.com").json().get("access_token")
    resp = list_reports(token_resp)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_report_by_id():
    register_user()
    token = login_user().json().get("access_token")
    resp = create_report(token, valid_payload)
    report_id = resp.json().get("id")
    resp2 = get_report(token, report_id)
    assert resp2.status_code == 200
    assert resp2.json().get("id") == report_id


def test_invalid_report_id():
    register_user()
    token = login_user().json().get("access_token")
    resp = get_report(token, "non-existent-id")
    assert resp.status_code == 404


def test_invalid_category():
    register_user()
    token = login_user().json().get("access_token")
    payload = dict(valid_payload)
    payload["category"] = "NOT_A_CATEGORY"
    resp = create_report(token, payload)
    assert resp.status_code == 422


def test_invalid_severity():
    register_user()
    token = login_user().json().get("access_token")
    payload = dict(valid_payload)
    payload["severity"] = "UNKNOWN"
    resp = create_report(token, payload)
    assert resp.status_code == 422
