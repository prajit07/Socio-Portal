import secrets
import string
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.models.org import University, UniversityMember
from app.models.enums import RoleEnum
from app.schemas.org import UniversityCreate, UniversityOut, UniversityMemberCreate, StudentBulkAdd, UniversitySuggest


router = APIRouter(prefix="/universities", tags=["universities"])


def _gen_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "Sc@" + "".join(secrets.choice(alphabet) for _ in range(8))


@router.post("", response_model=UniversityOut, status_code=status.HTTP_201_CREATED)
def create_university(
    payload: UniversityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in ("admin", "university_admin"):
        raise HTTPException(status_code=403, detail="Only admin or university_admin can create institutes")
    uni = University(**payload.model_dump())
    db.add(uni)
    db.flush()
    # Link the creator as an admin member of this institute.
    db.add(
        UniversityMember(
            university_id=uni.id,
            user_id=current_user.id,
            member_role="admin",
        )
    )
    db.commit()
    db.refresh(uni)
    return uni


@router.get("", response_model=list[UniversityOut])
def list_universities(
    search: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(University)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            University.name.ilike(like)
            | University.state.ilike(like)
            | University.district.ilike(like)
        )
    return q.order_by(University.name).limit(limit).all()


@router.get("/options", response_model=list[dict])
def list_options(
    search: Optional[str] = None,
    limit: int = 50000,
    db: Session = Depends(get_db),
):
    """Lightweight id+name directory for client-side autocomplete (fetched once)."""
    q = db.query(University.id, University.name)
    if search:
        q = q.filter(University.name.ilike(f"%{search.strip()}%"))
    return [{"id": uid, "name": nm} for uid, nm in q.order_by(University.name).limit(limit).all()]


@router.post("/suggest", response_model=UniversityOut, status_code=status.HTTP_201_CREATED)
def suggest_university(payload: UniversitySuggest, db: Session = Depends(get_db)):
    """Public: let a student add an institution missing from the directory."""
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Institution name required")
    existing = db.query(University).filter(University.name.ilike(name)).first()
    if existing:
        return existing
    uni = University(name=name, state=payload.state, verified=False)
    db.add(uni)
    db.commit()
    db.refresh(uni)
    return uni


@router.get("/{university_id}", response_model=UniversityOut)
def get_university(university_id: str, db: Session = Depends(get_db)):
    uni = db.get(University, university_id)
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
    return uni


def _require_uni_admin(db: Session, university_id: str, user: User) -> University:
    uni = db.get(University, university_id)
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
    if user.role.value == "admin":
        return uni
    member = (
        db.query(UniversityMember)
        .filter_by(university_id=university_id, user_id=user.id, member_role="admin")
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Only the institute admin can manage its students")
    return uni


@router.post("/{university_id}/members", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_member(
    university_id: str,
    payload: UniversityMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in ("admin", "university_admin"):
        raise HTTPException(status_code=403, detail="Not permitted")
    _require_uni_admin(db, university_id, current_user)
    uni = db.get(University, university_id)
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
    member = UniversityMember(
        university_id=university_id,
        user_id=payload.user_id,
        member_role=payload.member_role,
        department=payload.department,
        roll_number=payload.roll_number,
    )
    db.add(member)
    db.commit()
    return {"ok": True, "id": member.id}


@router.get("/{university_id}/members", response_model=list[dict])
def list_members(university_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_uni_admin(db, university_id, current_user)
    rows = (
        db.query(UniversityMember, User.name, User.email, User.role, User.is_email_verified)
        .join(User, User.id == UniversityMember.user_id)
        .filter(UniversityMember.university_id == university_id)
        .all()
    )
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "member_role": m.member_role,
            "department": m.department,
            "roll_number": m.roll_number,
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "is_email_verified": u.is_email_verified,
        }
        for m, u, _, _ in rows
    ]


@router.get("/{university_id}/students", response_model=list[dict])
def list_students(university_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List students of an institute with their department & roll number for clear identification."""
    _require_uni_admin(db, university_id, current_user)
    rows = (
        db.query(UniversityMember, User.name, User.email, User.is_email_verified)
        .join(User, User.id == UniversityMember.user_id)
        .filter(UniversityMember.university_id == university_id, UniversityMember.member_role == "student")
        .all()
    )
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "department": m.department,
            "roll_number": m.roll_number,
            "name": name,
            "email": email,
            "is_email_verified": is_email_verified,
        }
        for m, name, email, is_email_verified in rows
    ]


@router.post("/{university_id}/students/bulk", response_model=list[dict], status_code=status.HTTP_201_CREATED)
def bulk_add_students(
    university_id: str,
    payload: StudentBulkAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """HEI portal: create student accounts in bulk from a list.

    Each student gets a User (role=student, pre-verified) linked to this institute
    with their department and roll number so the HEI can identify them. A password is
    generated when not supplied (dev convenience — in production, email it instead).
    """
    _require_uni_admin(db, university_id, current_user)
    results = []
    for item in payload.students:
        existing = db.query(User).filter(User.email == item.email).first()
        if existing:
            results.append({"email": item.email, "status": "skipped", "reason": "email already registered"})
            continue
        password = item.password or _gen_password()
        student = User(
            name=item.name,
            email=item.email,
            password_hash=hash_password(password),
            role=RoleEnum.STUDENT,
            is_email_verified=True,
        )
        db.add(student)
        db.flush()
        db.add(
            UniversityMember(
                university_id=university_id,
                user_id=student.id,
                member_role="student",
                department=item.department,
                roll_number=item.roll_number,
            )
        )
        results.append(
            {"email": item.email, "user_id": student.id, "status": "created", "password": password}
        )
    db.commit()
    return results
