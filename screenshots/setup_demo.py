"""
Setup script: registers demo users, seeds problems/solutions/teams etc.,
then generates JWT tokens for each role. Tokens are saved to tokens.json.
"""
import requests
import json
import sys

BASE = "http://localhost:8000/api/v1"

USERS = {
    "citizen": {"name": "Ananya Sharma", "email": "demo_citizen@test.com", "password": "Demo1234!", "role": "citizen", "phone": "+919876543210"},
    "government": {"name": "Dr. Rajesh Kumar", "email": "demo_gov@test.com", "password": "Demo1234!", "role": "government", "phone": "+919876543211"},
    "admin": {"name": "System Admin", "email": "demo_admin@test.com", "password": "Demo1234!", "role": "admin", "phone": "+919876543212"},
    "student": {"name": "Priya Patel", "email": "demo_student@test.com", "password": "Demo1234!", "role": "student", "phone": "+919876543213"},
    "university_admin": {"name": "Prof. Srinivasan", "email": "demo_uni@test.com", "password": "Demo1234!", "role": "university_admin", "phone": "+919876543214"},
    "industry": {"name": "Vikram Mehta", "email": "demo_industry@test.com", "password": "Demo1234!", "role": "industry", "phone": "+919876543215"},
    "faculty": {"name": "Dr. Meena Iyer", "email": "demo_faculty@test.com", "password": "Demo1234!", "role": "faculty", "phone": "+919876543216"},
}

def register_users():
    print("=== Registering users ===")
    for role, data in USERS.items():
        try:
            r = requests.post(f"{BASE}/auth/register", json=data, timeout=10)
            if r.status_code == 201:
                print(f"  [OK] {role}: registered {data['email']}")
            elif r.status_code == 409:
                print(f"  [SKIP] {role}: already exists")
            else:
                print(f"  [ERR] {role}: {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"  [ERR] {role}: {e}")

def get_tokens():
    """Get JWT tokens by using the direct /auth/login endpoint (no OTP)."""
    print("\n=== Getting tokens ===")
    tokens = {}
    for role, data in USERS.items():
        try:
            r = requests.post(f"{BASE}/auth/login", data={
                "username": data["email"],
                "password": data["password"]
            }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
            if r.status_code == 200:
                token = r.json()["access_token"]
                tokens[role] = token
                print(f"  [OK] {role}: got token")
            else:
                print(f"  [ERR] {role}: {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"  [ERR] {role}: {e}")
    return tokens

def get_user_profiles(tokens):
    """Get user profiles for each role."""
    print("\n=== Getting profiles ===")
    profiles = {}
    for role, token in tokens.items():
        try:
            r = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
            if r.status_code == 200:
                profiles[role] = r.json()
                print(f"  [OK] {role}: {r.json().get('name')}")
            else:
                print(f"  [ERR] {role}: {r.status_code}")
        except Exception as e:
            print(f"  [ERR] {role}: {e}")
    return profiles

def seed_problems(tokens):
    """Seed some problems so dashboards have data."""
    print("\n=== Seeding problems ===")
    citizen_token = tokens.get("citizen")
    if not citizen_token:
        print("  [SKIP] No citizen token")
        return []
    
    problems_data = [
        {
            "title": "Broken Water Pipeline on MG Road",
            "description": "A major water pipeline burst near MG Road junction causing water wastage and flooding. The issue has been ongoing for 3 days and affects over 200 households.",
            "location": "MG Road, Bangalore, Karnataka",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "category": "water_sanitation",
        },
        {
            "title": "Illegal Dumping at Lake Boundary",
            "description": "Construction debris and household waste are being illegally dumped near Ulsoor Lake boundary. This is causing water pollution and affecting the local ecosystem.",
            "location": "Ulsoor Lake, Bangalore",
            "latitude": 12.9833,
            "longitude": 77.6200,
            "category": "environment",
        },
        {
            "title": "Poor Street Lighting in Residential Area",
            "description": "Multiple street lights are non-functional in Jayanagar 4th Block, creating safety concerns especially for women and elderly residents during night hours.",
            "location": "Jayanagar 4th Block, Bangalore",
            "latitude": 12.9259,
            "longitude": 77.5930,
            "category": "infrastructure",
        },
        {
            "title": "Overcrowded Government Hospital",
            "description": "Victoria Hospital is severely overcrowded with patients waiting 4-6 hours for basic consultation. The OPD section needs expansion and better queue management.",
            "location": "Victoria Hospital, Bangalore",
            "latitude": 12.9557,
            "longitude": 77.5723,
            "category": "healthcare",
        },
        {
            "title": "Lack of Digital Literacy in Rural Schools",
            "description": "Government schools in Ramanagara district have computers but no trained teachers for digital literacy. Students are missing out on essential tech skills.",
            "location": "Ramanagara District, Karnataka",
            "latitude": 12.7159,
            "longitude": 77.2806,
            "category": "education",
        },
        {
            "title": "Road Potholes Causing Accidents",
            "description": "Severe potholes on Old Airport Road near HAL have caused multiple two-wheeler accidents this month. Immediate repair needed.",
            "location": "Old Airport Road, Bangalore",
            "latitude": 12.9588,
            "longitude": 77.6468,
            "category": "infrastructure",
        },
        {
            "title": "Noise Pollution from Construction Site",
            "description": "A construction site near residential area in HSR Layout operates machinery at night violating noise pollution norms. Residents are unable to sleep.",
            "location": "HSR Layout, Bangalore",
            "latitude": 12.9116,
            "longitude": 77.6474,
            "category": "environment",
        },
        {
            "title": "Unemployment Among Youth in Dharwad",
            "description": "High youth unemployment rate in Dharwad district. Need skill development centers and industry connections for job placement.",
            "location": "Dharwad, Karnataka",
            "latitude": 15.4589,
            "longitude": 75.0078,
            "category": "employment",
        },
    ]
    
    problem_ids = []
    headers = {"Authorization": f"Bearer {citizen_token}"}
    for p in problems_data:
        try:
            r = requests.post(f"{BASE}/problems", json=p, headers=headers, timeout=10)
            if r.status_code in (200, 201):
                pid = r.json().get("id")
                problem_ids.append(pid)
                print(f"  [OK] Created problem: {p['title'][:40]}... (id={pid})")
            elif r.status_code == 409:
                print(f"  [SKIP] Already exists: {p['title'][:40]}...")
            else:
                print(f"  [ERR] {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"  [ERR] {e}")
    return problem_ids

def seed_university(tokens):
    """Create a university for university_admin."""
    print("\n=== Seeding university ===")
    token = tokens.get("university_admin")
    if not token:
        print("  [SKIP] No university_admin token")
        return None
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.post(f"{BASE}/universities", json={
            "name": "Indian Institute of Technology Bangalore",
            "city": "Bangalore",
            "state": "Karnataka",
        }, headers=headers, timeout=10)
        if r.status_code in (200, 201):
            uid = r.json().get("id")
            print(f"  [OK] Created university (id={uid})")
            return uid
        else:
            print(f"  [INFO] {r.status_code}: {r.text[:100]}")
            # Try to get existing
            r2 = requests.get(f"{BASE}/universities/mine", headers=headers, timeout=10)
            if r2.status_code == 200:
                data = r2.json()
                if data:
                    uid = data.get("id") if isinstance(data, dict) else data[0].get("id") if isinstance(data, list) and len(data) > 0 else None
                    if uid:
                        print(f"  [OK] Using existing university (id={uid})")
                        return uid
    except Exception as e:
        print(f"  [ERR] {e}")
    return None

def seed_industry(tokens):
    """Create an industry profile."""
    print("\n=== Seeding industry ===")
    token = tokens.get("industry")
    if not token:
        print("  [SKIP] No industry token")
        return None
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.post(f"{BASE}/industries", json={
            "name": "CleanTech Solutions Pvt. Ltd.",
            "type": "startup",
            "domain_tags": ["environment", "water_sanitation", "infrastructure"],
        }, headers=headers, timeout=10)
        if r.status_code in (200, 201):
            iid = r.json().get("id")
            print(f"  [OK] Created industry (id={iid})")
            return iid
        else:
            print(f"  [INFO] {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  [ERR] {e}")
    return None

def main():
    print("Checking backend health...")
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Backend: {r.json()}")
    except:
        print("ERROR: Backend not reachable!")
        sys.exit(1)
    
    register_users()
    tokens = get_tokens()
    profiles = get_user_profiles(tokens)
    problem_ids = seed_problems(tokens)
    uni_id = seed_university(tokens)
    ind_id = seed_industry(tokens)
    
    # Save everything
    result = {
        "tokens": tokens,
        "profiles": profiles,
        "problem_ids": problem_ids,
        "university_id": uni_id,
        "industry_id": ind_id,
    }
    
    outpath = r"c:\Users\praji\OneDrive\Desktop\SIH\screenshots\demo_tokens.json"
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n=== Saved to {outpath} ===")
    print(f"Tokens for roles: {list(tokens.keys())}")
    print(f"Problems created: {len(problem_ids)}")

if __name__ == "__main__":
    main()
