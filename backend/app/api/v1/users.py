from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=list[dict])
def search_users(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find platform users (students/faculty) by name or email so team leads can
    invite collaborators. Solvers only — citizens/government are not searchable."""
    if current_user.role.value not in ("student", "faculty", "university_admin", "admin"):
        raise HTTPException(status_code=403, detail="Only university members can search collaborators")
    q = q.strip()
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    rows = (
        db.query(User)
        .filter(
            User.role.in_(["student", "faculty"]),
            (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%")),
        )
        .order_by(User.name)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "is_email_verified": u.is_email_verified,
        }
        for u in rows
    ]