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


valid_payload = {
    "title": "Test Incident",
    "description": "Something happened",
    "category": "SAFETY",
    "severity": "LOW",
    "location_text": "Building A",
}


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


def test_assess_endpoint_and_rbac():
    # create reporter and report
    register_user(name="Rep", email="rep_risk@example.com")
    token = login_user(email="rep_risk@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    assert resp.status_code == 201
    incident_id = resp.json().get("id")

    # reporter cannot create assessment
    resp_r = client.post("/api/v1/risk/assess", json={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token}"})
    assert resp_r.status_code == 403

    # responder can
    token_resp = _make_admin_or_resp("resp_risk@example.com", "RESPONDER")
    resp2 = client.post("/api/v1/risk/assess", json={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token_resp}"})
    assert resp2.status_code == 201
    data = resp2.json()
    assert data["incident_id"] == incident_id

    # reporter can read own assessment
    # get assessment id from list for the incident
    resp_list = client.get(f"/api/v1/incidents/{incident_id}/risk", headers={"Authorization": f"Bearer {token}"})
    assert resp_list.status_code == 200
    arr = resp_list.json()
    assert isinstance(arr, list)
    assert len(arr) >= 1

    # other reporter cannot read
    register_user(name="Other", email="other@example.com")
    token_other = login_user(email="other@example.com").json().get("access_token")
    resp_other = client.get(f"/api/v1/incidents/{incident_id}/risk", headers={"Authorization": f"Bearer {token_other}"})
    assert resp_other.status_code == 403
