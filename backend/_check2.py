from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.problem import Problem

c = TestClient(app)
r = c.post("/api/v1/auth/register", json={"email": "putertest@example.com", "password": "Test@1234", "full_name": "PT", "role": "citizen", "domain_tags": []})
print("register:", r.status_code, r.text[:300])
tok = c.post("/api/v1/auth/login", data={"username": "putertest@example.com", "password": "Test@1234"}).json().get("access_token")
print("token present:", bool(tok))

H = {"Authorization": f"Bearer {tok}"}

p = c.post("/api/v1/problems", json={"title": "Pipe issue", "description": "Something about pipes", "tags": []}, headers=H).json()
pid = p["id"]

# Upload audio evidence with a CLIENT-supplied transcript (Puter path)
audio = b"FAKEAUDIODATA"
files = {"file": ("note.webm", audio, "audio/webm")}
data = {"type": "audio", "transcript": "The main water pipe burst and flooded the entire street near the school."}
ev = c.post(f"/api/v1/problems/{pid}/evidence", files=files, data=data, headers=H).json()
print("evidence.transcript:", ev["transcript"])

db = SessionLocal()
prob = db.query(Problem).filter(Problem.id == pid).first()
print("problem.evidence_text:", repr(prob.evidence_text))
print("problem.ai_category:", prob.ai_category)
db.close()

assert ev["transcript"] and "water pipe burst" in ev["transcript"]
assert prob.evidence_text and "water pipe burst" in prob.evidence_text
print("PUTER CLIENT-TRANSCRIPT PATH OK")
