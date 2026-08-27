"""Smoke test: Phase 1 (auth) -> Phase 2 (citizen submit + evidence) -> Phase 3 (AI pipeline + routing)."""
import sys, os
sys.path.append(os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def j(r): return r.json()

# --- Phase 1: register + login (citizen) ---
import uuid
EMAIL = f"citizen_{uuid.uuid4().hex[:8]}@demo.com"
r = client.post("/api/v1/auth/register", json={
    "name": "Test Citizen", "email": EMAIL,
    "password": "Test@1234", "role": "citizen"
})
assert r.status_code in (200, 201), j(r)
print("Register:", r.status_code)

r = client.post("/api/v1/auth/login", data={"username": EMAIL, "password": "Test@1234"})
assert r.status_code == 200, j(r)
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}
print("Login OK, token len", len(token))

me = client.get("/api/v1/auth/me", headers=H).json()
print("Me:", me["role"], me["id"])

# --- Phase 2: submit problem (triggers Phase 3 AI pipeline) ---
r = client.post("/api/v1/problems", headers=H, json={
    "title": "Sewage overflow near community park",
    "description": "Raw sewage has been leaking onto the street for two weeks, creating a health hazard and foul smell affecting residents.",
    "address": "Sector 12, Dwarka, New Delhi",
    "latitude": 28.59, "longitude": 77.04,
    "tags": ["water", "sanitation"]
})
assert r.status_code == 201, j(r)
prob = r.json()
print("Problem created:", prob["id"], "| status:", prob["status"],
      "| ai_category:", prob["ai_category"], "| priority:", prob["ai_priority"],
      "| ai_tags:", prob["ai_tags"])
assert prob["status"] in ("open", "duplicate"), prob["status"]

# --- Phase 2: upload audio evidence (voice-to-text mock) ---
audio = b"RIFF....fake-wav-bytes"
r = client.post(f"/api/v1/problems/{prob['id']}/evidence",
                headers=H,
                files={"file": ("voice_note.wav", audio, "audio/wav")},
                data={"type": "audio"})
assert r.status_code == 201, j(r)
ev = r.json()
print("Evidence uploaded:", ev["type"], "| transcript:", (ev["transcript"] or "")[:40], "...")

# --- Phase 3: re-analyze explicitly ---
r = client.post(f"/api/v1/ai/analyze/{prob['id']}", headers=H)
assert r.status_code == 200, j(r)
print("Analyze:", j(r))

# --- notifications for citizen + routing recipients ---
notifs = client.get("/api/v1/notifications", headers=H).json()
print("Citizen notifications:", len(notifs))

# Login as university_admin (HEI) -> should have a routing notification
r = client.post("/api/v1/auth/login", data={"username": "hei@demo.com", "password": "Test@1234"})
ht = {"Authorization": f"Bearer {r.json()['access_token']}"}
hn = client.get("/api/v1/notifications", headers=ht).json()
print("HEI notifications (routed):", len(hn))
assert len(hn) >= 1, "HEI should be routed the problem"

# Login as industry (domain water_sanitation) -> should also be routed
r = client.post("/api/v1/auth/login", data={"username": "industry@demo.com", "password": "Test@1234"})
hi = {"Authorization": f"Bearer {r.json()['access_token']}"}
inp = client.get("/api/v1/notifications", headers=hi).json()
print("Industry notifications (routed):", len(inp))
assert len(inp) >= 1, "Industry should be routed (tag match)"

# --- tags taxonomy ---
tags = client.get("/api/v1/tags", headers=H).json()
print("Taxonomy tags:", len(tags))

print("\nALL PHASE 1-3 BACKEND CHECKS PASSED [OK]")
