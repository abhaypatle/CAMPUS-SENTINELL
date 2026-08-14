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


def test_trigger_endpoint_and_idempotency_and_rbac():
    # create reporter and report
    register_user(name="Rep", email="rep_es@example.com")
    token = login_user(email="rep_es@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    assert resp.status_code == 201
    incident_id = resp.json().get("id")

    # create assessment as responder
    token_resp = _make_admin_or_resp("resp_es@example.com", "RESPONDER")
    r2 = client.post("/api/v1/risk/assess", json={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token_resp}"})
    assert r2.status_code == 201

    # trigger as reporter should be forbidden
    resp_forbid = client.post("/api/v1/escalations/trigger", params={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token}"})
    assert resp_forbid.status_code == 403

    # trigger as responder
    resp_trig = client.post("/api/v1/escalations/trigger", params={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token_resp}"})
    assert resp_trig.status_code == 200
    data = resp_trig.json()

    # trigger again idempotent
    resp_trig2 = client.post("/api/v1/escalations/trigger", params={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token_resp}"})
    assert resp_trig2.status_code == 200
    assert resp_trig.json().get("id") == resp_trig2.json().get("id")

    # reporter can get escalation list for own incident
    resp_list = client.get(f"/api/v1/incidents/{incident_id}/escalations", headers={"Authorization": f"Bearer {token}"})
    assert resp_list.status_code == 200
    arr = resp_list.json()
    assert isinstance(arr, list)

    # other reporter can't get
    register_user(name="Other", email="other2@example.com")
    token_other = login_user(email="other2@example.com").json().get("access_token")
    resp_other = client.get(f"/api/v1/incidents/{incident_id}/escalations", headers={"Authorization": f"Bearer {token_other}"})
    assert resp_other.status_code == 403
