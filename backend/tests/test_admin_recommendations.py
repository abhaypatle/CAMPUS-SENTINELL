import sys
import os

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


def test_admin_intelligence_includes_recommendations():
    register_user(name="Rep", email="rep_ai@example.com")
    token = login_user(email="rep_ai@example.com").json().get("access_token")
    resp = create_report(token, valid_payload)
    incident_id = resp.json().get("id")

    token_resp = _make_admin_or_resp("resp_ai@example.com", "RESPONDER")
    # generate recommendation
    r = client.post("/api/v1/recommendations/generate", params={"incident_id": incident_id}, headers={"Authorization": f"Bearer {token_resp}"})
    assert r.status_code == 200

    # fetch admin intelligence
    ai = client.get(f"/api/v1/admin/incidents/{incident_id}/intelligence", headers={"Authorization": f"Bearer {token_resp}"})
    assert ai.status_code == 200
    data = ai.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
