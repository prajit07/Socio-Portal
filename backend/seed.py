"""Seed taxonomy tags + demo accounts for local testing."""
import os
import sys
import json

sys.path.append(os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.tag import Tag
from app.models.enums import RoleEnum

TAXONOMY = os.path.join(os.path.dirname(__file__), "app", "ml", "taxonomy.json")


def main():
    db = SessionLocal()
    try:
        # Seed tags
        with open(TAXONOMY, "r", encoding="utf-8") as f:
            cats = json.load(f)["categories"]
        for c in cats:
            if not db.query(Tag).filter(Tag.id == c["id"]).first():
                db.add(Tag(id=c["id"], name=c["name"], description=c.get("name")))
        db.commit()
        print(f"Seeded {len(cats)} tags.")

        # Demo users
        demos = [
            ("prajitjanakiraman@gmail.com", "Prajit Demo", "Test@1234", RoleEnum.CITIZEN, None),
            ("industry@demo.com", "Acme Innovations", "Test@1234", RoleEnum.INDUSTRY, ["water_sanitation", "waste_management"]),
            ("hei@demo.com", "Demo University", "Test@1234", RoleEnum.UNIVERSITY_ADMIN, None),
        ]
        created = 0
        for email, name, pw, role, tags in demos:
            if not db.query(User).filter(User.email == email).first():
                u = User(name=name, email=email, password_hash=hash_password(pw), role=role, domain_tags=tags)
                db.add(u)
                created += 1
        db.commit()
        print(f"Created {created} demo users.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
