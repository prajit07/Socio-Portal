"""Auth endpoint tests.

Tests override DATABASE_URL with SQLite so the suite can run without a live
Neon connection. SQLAlchemy 2.0 supports both dialects; in-memory sqlite is
fine for these endpoint-level checks.
"""

import os

# Set BEFORE importing the app so Settings picks it up.
os.environ.setdefault("DATABASE_URL", "sqlite:///./_test_phase1.db")
os.environ.setdefault("JWT_SECRET", "test-secret-please-change-1234567890")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = os.environ["DATABASE_URL"]
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_register_success(client):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice Citizen",
            "email": "alice@example.com",
            "password": "supersecret123",
            "role": "citizen",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "citizen"
    assert "password_hash" not in body
    assert "id" in body


def test_register_duplicate_email_returns_409(client):
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        "password": "supersecret123",
        "role": "student",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_returns_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Carol",
            "email": "carol@example.com",
            "password": "supersecret123",
            "role": "faculty",
        },
    )
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "carol@example.com", "password": "supersecret123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password_returns_401(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Dan",
            "email": "dan@example.com",
            "password": "supersecret123",
            "role": "industry",
        },
    )
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "dan@example.com", "password": "WRONG"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_valid_token_returns_user(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Eve",
            "email": "eve@example.com",
            "password": "supersecret123",
            "role": "government",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "eve@example.com", "password": "supersecret123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "eve@example.com"
    assert r.json()["role"] == "government"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
