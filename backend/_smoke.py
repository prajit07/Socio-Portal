import random, string
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
def rand(prefix): return prefix + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

def register(role, name="Test"):
    email = rand("u") + "@example.com"
    r = c.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "Test@1234", "role": role})
    assert r.status_code in (201, 200), (r.status_code, r.text)
    lr = c.post("/api/v1/auth/login", data={"username": email, "password": "Test@1234"})
    assert lr.status_code == 200, (lr.status_code, lr.text)
    return lr.json()["access_token"], email

def auth(t): return {"Authorization": f"Bearer {t}"}

print("== register actors ==")
ctz_t, ctz_e = register("citizen")
uad_t, _ = register("university_admin", "UniAdmin")
stu_t, _ = register("student", "Student")
ind_t, _ = register("industry", "Ind")
gov_t, _ = register("government", "Gov")

print("== citizen submits problem ==")
pr = c.post("/api/v1/problems", json={"title": "Water leakage in sector 12", "description": "Pipe burst causing flooding for weeks", "tags": ["water"]}, headers=auth(ctz_t))
assert pr.status_code == 201, (pr.status_code, pr.text)
pid = pr.json()["id"]
print("problem", pid, pr.json()["status"], pr.json()["ai_category"])

print("== university_admin creates university ==")
ur = c.post("/api/v1/universities", json={"name": "Demo HEI", "district": "Delhi", "state": "Delhi"}, headers=auth(uad_t))
assert ur.status_code == 201, (ur.status_code, ur.text)
uid = ur.json()["id"]

print("== student forms team ==")
tr = c.post("/api/v1/teams", json={"problem_id": pid, "name": "Team A", "university_id": uid}, headers=auth(stu_t))
assert tr.status_code == 201, (tr.status_code, tr.text)
tid = tr.json()["id"]

print("== student submits proposal ==")
pp = c.post("/api/v1/proposals", json={"team_id": tid, "problem_id": pid, "title": "Low-cost valve fix", "description": "Replace valves with community funding"}, headers=auth(stu_t))
assert pp.status_code == 201, (pp.status_code, pp.text)
propid = pp.json()["id"]

print("== university_admin approves proposal ==")
ap = c.post(f"/api/v1/proposals/{propid}/approve", headers=auth(uad_t))
assert ap.status_code == 200, (ap.status_code, ap.text)
print("proposal status", ap.json()["status"])

print("== industry creates org + expresses interest ==")
ir = c.post("/api/v1/industries", json={"name": "Acme Tech", "type": "startup", "domain_tags": ["water"]}, headers=auth(ind_t))
assert ir.status_code == 201, (ir.status_code, ir.text)
iid = ir.json()["id"]
cr = c.post("/api/v1/collaborations", json={"proposal_id": propid, "industry_id": iid, "notes": "happy to fund"}, headers=auth(ind_t))
assert cr.status_code == 201, (cr.status_code, cr.text)
colid = cr.json()["id"]
print("collaboration", colid, cr.json()["stage"])

print("== add milestone + impact ==")
mr = c.post(f"/api/v1/collaborations/{colid}/milestones", json={"title": "Prototype build", "due_date": "2026-09-30T00:00:00Z"}, headers=auth(ind_t))
assert mr.status_code == 201, (mr.status_code, mr.text)
im = c.post(f"/api/v1/collaborations/{colid}/impact", json={"beneficiaries_count": 1200, "impact_summary": "Clean water restored", "district": "Delhi"}, headers=auth(ind_t))
assert im.status_code == 201, (im.status_code, im.text)

print("== engagement: comment + upvote ==")
cm = c.post("/api/v1/engagement/comments", json={"entity_type": "problem", "entity_id": pid, "content": "Hope this gets fixed"}, headers=auth(ctz_t))
assert cm.status_code == 201, (cm.status_code, cm.text)
uv = c.post("/api/v1/engagement/upvotes", json={"problem_id": pid}, headers=auth(ctz_t))
assert uv.status_code == 200, (uv.status_code, uv.text)
print("upvote", uv.json())

print("== government analytics ==")
ga = c.get("/api/v1/government/analytics", headers=auth(gov_t))
assert ga.status_code == 200, (ga.status_code, ga.text)
print("kpis", ga.json()["kpis"])

print("== admin: list users (expect 403 for non-admin) ==")
au = c.get("/api/v1/admin/users", headers=auth(ctz_t))
assert au.status_code == 403, au.status_code
print("admin gate 403 OK")

print("\nALL SMOKE CHECKS PASSED")
