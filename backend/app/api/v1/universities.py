from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.org import University, UniversityMember
from app.schemas.org import UniversityCreate, UniversityOut, UniversityMemberCreate

router = APIRouter(prefix="/universities", tags=["universities"])


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
    db.commit()
    db.refresh(uni)
    return uni


@router.get("", response_model=list[UniversityOut])
def list_universities(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(University).order_by(University.name).all()


@router.get("/{university_id}", response_model=UniversityOut)
def get_university(university_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uni = db.get(University, university_id)
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
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
    uni = db.get(University, university_id)
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
    member = UniversityMember(
        university_id=university_id,
        user_id=payload.user_id,
        member_role=payload.member_role,
    )
    db.add(member)
    db.commit()
    return {"ok": True, "id": member.id}


@router.get("/{university_id}/members", response_model=list[dict])
def list_members(university_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(UniversityMember, User.name, User.email, User.role)
        .join(User, User.id == UniversityMember.user_id)
        .filter(UniversityMember.university_id == university_id)
        .all()
    )
    return [
        {"id": m.id, "user_id": m.user_id, "member_role": m.member_role, "name": u.name, "email": u.email, "role": u.role.value}
        for m, u, _ in rows
    ]
