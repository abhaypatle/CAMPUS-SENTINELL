import json
import sys
import os
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

# Ensure backend (project root for the python package) is on path for imports during tests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.db.session import engine, SessionLocal, Base
from src.models.user import User
from src.auth.hash import verify_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    # Create tables and clear users table before each test
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    yield


def register_user(name="Test User", email="test@example.com", password="password123"):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    return resp


def login_user(email="test@example.com", password="password123"):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp


def test_successful_registration():
    resp = register_user()
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["role"] == "REPORTER"
    assert "password_hash" not in data


def test_duplicate_registration():
    resp1 = register_user()
    assert resp1.status_code == 201
    resp2 = register_user()
    assert resp2.status_code == 409


def test_password_is_hashed():
    register_user()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.password_hash != "password123"
        assert verify_password("password123", user.password_hash)
    finally:
        db.close()


def test_successful_login():
    register_user()
    resp = login_user()
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_password():
    register_user()
    resp = login_user(password="wrongpass")
    assert resp.status_code == 401


def test_unknown_email():
    resp = login_user(email="noone@example.com")
    assert resp.status_code == 401


def test_me_with_valid_token():
    register_user()
    login = login_user()
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"


def test_me_without_token():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token():
    headers = {"Authorization": "Bearer invalid.token.here"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401


def test_default_role_is_reporter():
    resp = register_user()
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "REPORTER"
