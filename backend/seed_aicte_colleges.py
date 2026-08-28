"""Seed the AICTE Indian colleges dataset (from indian-colleges-list.vercel.app)
into the universities directory. Idempotent by case-insensitive name.

Requires colleges.json (downloaded earlier) at the path below.
Run: python seed_aicte_colleges.py
"""
import sys
import json

sys.path.insert(0, r"C:\Users\praji\OneDrive\Desktop\SIH\backend")

from app.core.database import SessionLocal
from app.models.org import University
from sqlalchemy import insert

JSON_PATH = r"C:\Users\praji\AppData\Local\Temp\opencode\colleges.json"


def main():
    with open(JSON_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    items = payload.get("data", [])
    print(f"Loaded {len(items)} colleges from JSON")

    db = SessionLocal()
    existing = {n.lower() for (n,) in db.query(University.name).all()}
    rows = []
    seen = set()
    for it in items:
        nm = (it.get("institute_name") or "").strip()
        if not nm:
            continue
        key = nm.lower()
        if key in existing or key in seen:
            continue
        seen.add(key)
        rows.append({
            "name": nm,
            "address": (it.get("address") or "")[:500],
            "district": (it.get("district") or "")[:100],
            "verified": True,
        })

    print(f"New colleges to insert: {len(rows)}")
    chunk = 5000
    for i in range(0, len(rows), chunk):
        db.execute(insert(University), rows[i:i + chunk])
    db.commit()
    total = db.query(University).count()
    db.close()
    print(f"Done. Total institutions in directory: {total}")


if __name__ == "__main__":
    main()
