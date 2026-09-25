"""Student workflow verification (v2 — after self-link + email invite fix).

Tests the NEW student journey:
  1. Student registers WITHOUT an institute.
  2. Student tries to form a team -> 403 (institute mandatory) -> proves block.
  3. Student self-links to an institute (new POST /universities/{id}/self-link).
  4. Student forms a team on an open problem (must use their linked institute).
  5. Team lead invites a collaborator BY EMAIL (befriend a second student).
  6. Invited student also self-links; together they propose a solution -> submit.
  7. Permission check: non-member cannot add members to a team they don't belong to.
"""
import json
import sys
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://localhost:8000/api/v1"
OUT = []


def req(method, path, token=None, json_body=None, form=None):
    url = BASE + path
    headers = {}
    body = None
    if json_body is not None:
        body = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    elif form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode()
            code = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        code = e.code
    except urllib.error.URLError as e:
        return "NETERR", str(e)
    try:
        data = json.loads(raw)
    except Exception:
        data = raw[:400]
    return code, data


def log(*a):
    m = " ".join(str(x) for x in a)
    OUT.append(m)
    print(m, flush=True)


def login(email):
    s, d = req("POST", "/auth/login", json_body={"username": email, "password": "Test@1234"})
    if s == 200 and isinstance(d, dict) and "access_token" in d:
        return d["access_token"]
    r = urllib.request.Request(BASE + "/auth/login", data=urllib.parse.urlencode({"username": email, "password": "Test@1234"}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            d = json.loads(resp.read().decode())
        return d["access_token"]
    except Exception as e:
        log("login fail", email, e)
        return None


def assert_ok(cond, label):
    if not cond:
        raise AssertionError(label)


def main():
    tag = uuid.uuid4().hex[:6]
    e1 = f"stu.leader.{tag}@sih.in"
    e2 = f"stu.teammate.{tag}@sih.in"
    log("=" * 70)
    log(f"STUDENT FLOW v2 — tag {tag}")

    # 0. pick a university and an open problem
    s, unis = req("GET", "/universities/options?limit=5")
    assert_ok(s == 200 and unis, "fetch universities")
    uid = unis[0]["id"]
    uni_name = unis[0]["name"]
    log(f"university: {uni_name} ({uid})")

    s, probs = req("GET", "/problems?limit=200")
    assert_ok(s == 200, "list problems")
    open_prob = next((p for p in probs if p.get("status") in ("open", "validated")), None)
    if not open_prob:
        log("no open problem found — creating one as citizen")
        s, c = req("POST", "/auth/register", json_body={"name": "WF Citizen", "email": f"wf.citizen.{tag}@sih.in", "password": "Test@1234", "role": "citizen"})
        ct = login(f"wf.citizen.{tag}@sih.in")
        s, c = req("POST", "/problems", json_body={"title": f"Open test problem {tag}", "description": f"Unique desc {tag} for student flow verification.", "address": "Kuthambakkam village, Tiruvallur district, Tamil Nadu"}, token=ct)
        open_prob = c
        log(f"created problem {c.get('id')}")
    pid = open_prob["id"]
    log(f"problem: {pid} ({open_prob.get('status')})")

    # 1. register two students WITHOUT institute
    s, d = req("POST", "/auth/register", json_body={"name": "Otto Leader", "email": e1, "password": "Test@1234", "role": "student"})
    s2, d2 = req("POST", "/auth/register", json_body={"name": "Mia Teammate", "email": e2, "password": "Test@1234", "role": "student"})
    t1 = login(e1)
    t2 = login(e2)
    assert_ok(t1 and t2, "both students log in")

    # 2. student tries to form a team without an institute -> must be blocked
    s, d = req("POST", "/teams", json_body={"problem_id": pid, "name": f"Unlinked Team {tag}", "university_id": None}, token=t1)
    log(f"create team w/o institute: {s} — {d if s != 201 else 'UNEXPECTED OK'}")
    assert_ok(s == 403 and "linked" in str(d).lower(), "unlinked student blocked (403)")

    # 3. self-link both students
    s, d = req("POST", f"/universities/{uid}/self-link", json_body={}, token=t1)
    log(f"self-link leader: {s} {d}")
    assert_ok(s in (200, 201), "leader self-link ok")
    s, d2r = req("POST", f"/universities/{uid}/self-link", json_body={"department": "CSE", "roll_number": "21CS" + tag[:4]}, token=t2)
    log(f"self-link teammate: {s} {d2r}")
    assert_ok(s in (200, 201), "teammate self-link ok")

    # verify member-of now returns the institute
    s, mine = req("GET", "/universities/member-of", token=t1)
    log(f"leader member-of: {s} {[m['id'] for m in mine] if isinstance(mine, list) else mine}")
    assert_ok(s == 200 and any(m["id"] == uid for m in mine), "leader sees membership")

    # 4. form a team with linked institute
    s, team = req("POST", "/teams", json_body={"problem_id": pid, "name": f"HydroFix {tag}", "university_id": uid}, token=t1)
    log(f"create team: {s} {team.get('id') if isinstance(team, dict) else team}")
    assert_ok(s == 201 and isinstance(team, dict) and team.get("id"), "team created")
    tid = team["id"]

    # 4b. team cannot be formed under a foreign institute
    s, unis2 = req("GET", "/universities/options?limit=5&search=ANNA")
    other = next((x for x in unis2 if x["id"] != uid), None)
    if other:
        s, d = req("POST", "/teams", json_body={"problem_id": pid, "name": f"WrongInst {tag}", "university_id": other["id"]}, token=t1)
        log(f"create team under foreign institute: {s} — {d if s != 403 else str(d)}")
        assert_ok(s == 403, "foreign institute rejected")

    # 5. invite teammate BY EMAIL
    s, d = req("POST", f"/teams/{tid}/members", json_body={"email": e2}, token=t1)
    log(f"invite by email: {s} {d}")
    assert_ok(s == 201, "member added by email")

    # 6. teammate proposes from the team, then submits
    s, prop = req("POST", "/proposals", json_body={
        "team_id": tid,
        "problem_id": pid,
        "title": f"Solar-powered water ATMs {tag}",
        "description": f"Community-run solar water ATMs with IoT monitoring {tag}.",
        "estimated_budget": "250000",
        "estimated_timeline": "6 months",
        "document_urls": ["https://example.com/spec.pdf"],
    }, token=t2)
    log(f"create proposal (teammate): {s} {prop.get('id') if isinstance(prop, dict) else prop}")
    assert_ok(s == 201 and isinstance(prop, dict) and prop.get("id"), "proposal drafted")
    spid = prop["id"]
    # submit is author-scoped: a non-author team lead must be rejected
    s, d = req("POST", f"/proposals/{spid}/submit", token=t1)
    log(f"submit proposal as non-author team lead: {s} — {d if s != 200 else 'UNEXPECTED OK'}")
    assert_ok(s == 403, "non-author cannot submit")
    # the author (teammate t2) submits
    s, d = req("POST", f"/proposals/{spid}/submit", token=t2)
    log(f"submit proposal as author: {s} — {d.get('status') if isinstance(d, dict) else d}")
    assert_ok(s == 200, "proposal submitted")

    # 7. permission check: an outside student cannot add members
    e3 = f"stu.outsider.{tag}@sih.in"
    req("POST", "/auth/register", json_body={"name": "Eve Outsider", "email": e3, "password": "Test@1234", "role": "student"})
    t3 = login(e3)
    s, d = req("POST", f"/teams/{tid}/members", json_body={"email": e3}, token=t3)
    log(f"outsider add on foreign team: {s} — {d if s == 403 else 'UNEXPECTED OK'}")
    assert_ok(s == 403, "outsider cannot add members")

    # 8. team list scoped: outsider does not see the team; leader/teammate do
    s, tl = req("GET", "/teams", token=t1)
    assert_ok(s == 200 and any(x["id"] == tid for x in tl), "leader sees team")
    s, tl3 = req("GET", "/teams", token=t3)
    assert_ok(s == 200 and not any(x["id"] == tid for x in tl3), "outsider does not see team")

    # 9. user search returns the teammate
    s, hits = req("GET", "/users/search", token=t1, json_body=None)
    log(f"search without q: {s}")
    assert_ok(s in (400, 422), "search requires q (400/422 ok)")
    s, hits = req("GET", "/users/search?q=Otto%20Leader", token=t1)
    log(f"user search 'Otto Leader': {s} {[(h['name'], h['role']) for h in hits] if isinstance(hits, list) else hits}")
    assert_ok(s == 200 and isinstance(hits, list) and any(h["id"] == team["created_by"] or h["email"] == e1 for h in hits), "search finds leader")

    log("=" * 70)
    log("STUDENT FLOW v2: ALL CHECKS PASSED")
    log(f"  leader={e1} teammate={e2} problem={pid} team={tid} proposal={spid}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()