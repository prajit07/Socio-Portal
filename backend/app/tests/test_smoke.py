"""End-to-end smoke tests covering the full lifecycle.

Register → Login → Submit Problem → AI Pipeline (stubbed) → Government
Analytics; plus the Industry → Collaboration → Engagement lifecycle.

Uses SQLite override (same pattern as test_auth.py) so the suite runs
without a live Neon connection.
"""
import os

# Set BEFORE importing the app so Settings picks it up.
os.environ.setdefault("DATABASE_URL", "sqlite:///./_test_smoke.db")
os.environ.setdefault("JWT_SECRET", "test-smoke-secret-1234567890")
os.environ.setdefault("LORA_PROVIDER", "off")
os.environ.setdefault("CLOUDFLARE_ACCOUNT_ID", "")
os.environ.setdefault("CLOUDFLARE_API_TOKEN", "")

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


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _register(client, email, role="citizen"):
    r = client.post(
        "/api/v1/auth/register",
        json={"name": email.split("@")[0], "email": email, "password": "TestPass123", "role": role},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _login(client, email, password="TestPass123"):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Citizen lifecycle: register → login → submit problem → list
# ---------------------------------------------------------------------------

class TestCitizenLifecycle:
    def test_register_login_me(self, client):
        _register(client, "citizen1@demo.com")
        token = _login(client, "citizen1@demo.com")
        r = client.get("/api/v1/auth/me", headers=_auth_header(token))
        assert r.status_code == 200
        assert r.json()["email"] == "citizen1@demo.com"
        assert r.json()["role"] == "citizen"

    def test_submit_problem_as_citizen(self, client):
        _register(client, "citizen2@demo.com")
        token = _login(client, "citizen2@demo.com")
        r = client.post(
            "/api/v1/problems",
            json={
                "title": "Broken streetlight near park",
                "description": "The streetlight at MG Road junction has been off for 3 nights.",
                "latitude": 12.9716,
                "longitude": 77.5946,
            },
            headers=_auth_header(token),
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["title"] == "Broken streetlight near park"
        assert body["status"] == "pending_validation"
        assert "id" in body

    def test_list_problems_includes_created(self, client):
        _register(client, "citizen3@demo.com")
        token = _login(client, "citizen3@demo.com")
        client.post(
            "/api/v1/problems",
            json={"title": "Water logging", "description": "Main road flooded."},
            headers=_auth_header(token),
        )
        r = client.get("/api/v1/problems", headers=_auth_header(token))
        assert r.status_code == 200
        problems = r.json()
        assert any(p["title"] == "Water logging" for p in problems)


# ---------------------------------------------------------------------------
# Industry lifecycle: collab with Fund/Co-Develop + testing/IP payloads
# ---------------------------------------------------------------------------

class TestIndustryLifecycle:
    def _seed_proposal(self, client):
        """citizen problem → university_admin team → proposal → returns solution id."""
        _register(client, "cit4@demo.com")
        ctoken = _login(client, "cit4@demo.com")
        problem = client.post(
            "/api/v1/problems",
            json={"title": "Street Food Hygiene", "description": "Street vendors lack hygiene."},
            headers=_auth_header(ctoken),
        ).json()

        _register(client, "uni1@demo.com", role="university_admin")
        utoken = _login(client, "uni1@demo.com")
        team = client.post(
            "/api/v1/teams",
            json={"problem_id": problem["id"], "name": "Hygiene Team"},
            headers=_auth_header(utoken),
        )
        assert team.status_code == 201, team.text
        proposal = client.post(
            "/api/v1/proposals",
            json={
                "problem_id": problem["id"],
                "team_id": team.json()["id"],
                "title": "Vendor Hygiene Kit",
                "description": "Affordable hygiene kit for vendors",
                "estimated_budget": "INR 5L",
                "estimated_timeline": "6 months",
            },
            headers=_auth_header(utoken),
        )
        assert proposal.status_code == 201, proposal.text
        return ctoken, problem, proposal.json()

    def test_industry_creates_funded_collaboration(self, client):
        _, _, solution = self._seed_proposal(client)

        _register(client, "industry1@demo.com", role="industry")
        itoken = _login(client, "industry1@demo.com")
        industry = client.post(
            "/api/v1/industries",
            json={"name": "GreenTech", "type": "startup", "district": "Bengaluru", "state": "Karnataka"},
            headers=_auth_header(itoken),
        )
        assert industry.status_code == 201, industry.text

        collab = client.post(
            "/api/v1/collaborations",
            json={"proposal_id": solution["id"], "industry_id": industry.json()["id"], "stage": "interested", "engagement_type": "fund"},
            headers=_auth_header(itoken),
        )
        assert collab.status_code == 201, collab.text
        body = collab.json()
        assert body["engagement_type"] == "fund"
        assert body.get("startup_created") is False

        # Co-Develop + funding testing outcomes + startup flag via PATCH
        r = client.patch(
            f"/api/v1/collaborations/{body['id']}",
            json={"engagement_type": "co_develop", "funding_status": "committed", "testing_outcomes": "Pilot completed at 3 sites", "startup_created": True},
            headers=_auth_header(itoken),
        )
        assert r.status_code == 200, r.text
        assert r.json()["engagement_type"] == "co_develop"
        assert r.json()["funding_status"] == "committed"
        assert r.json()["testing_outcomes"] == "Pilot completed at 3 sites"
        assert r.json()["startup_created"] is True

        # IP record with a file upload
        uploaded = client.post(
            f"/api/v1/collaborations/{body['id']}/ip/upload",
            files={"file": ("patent.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={"type": "patent", "status": "filed", "reference_no": "IN2026/000123"},
            headers=_auth_header(itoken),
        )
        assert uploaded.status_code == 201, uploaded.text
        assert uploaded.json()["file_url"]
        assert uploaded.json()["type"] == "patent"

        # Detail reflects everything incl. file_url on the IP record
        detail = client.get(f"/api/v1/collaborations/{body['id']}", headers=_auth_header(itoken))
        assert detail.status_code == 200
        d = detail.json()
        assert d["engagement_type"] == "co_develop"
        assert d["funding_status"] == "committed"
        assert d["testing_outcomes"] == "Pilot completed at 3 sites"
        assert d["startup_created"] is True
        assert any(i.get("file_url") for i in d["ip_records"])


# ---------------------------------------------------------------------------
# Government analytics: problem + collab data flows into KPIs
# ---------------------------------------------------------------------------

class TestGovernmentAnalytics:
    def test_analytics_shape(self, client):
        # Seed one problem
        _register(client, "gov1@demo.com", role="government")
        gtoken = _login(client, "gov1@demo.com")

        _register(client, "c@demo.com")
        ctoken = _login(client, "c@demo.com")
        client.post(
            "/api/v1/problems",
            json={"title": "Illegal Dumping", "description": "Construction waste near lake."},
            headers=_auth_header(ctoken),
        )

        r = client.get("/api/v1/government/analytics", headers=_auth_header(gtoken))
        assert r.status_code == 200, r.text
        body = r.json()
        # Must contain key sections
        assert "overview" in body or "problems" in body or "kpis" in body, f"Unexpected shape: {list(body.keys())}"
