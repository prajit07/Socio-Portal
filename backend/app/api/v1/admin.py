from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.problem import Problem
from app.models.routing import Notification
from app.models.engagement import AuditLog
from app.models.enums import RoleEnum, ProblemStatusEnum, NotificationTypeEnum
from app.schemas.auth import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_email_verified: Optional[bool] = None


class StatusUpdate(BaseModel):
    status: str


class BroadcastIn(BaseModel):
    message: str
    role: Optional[str] = None  # if set, only that role; else all users


def _admin_only(current_user: User):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _admin_only(current_user)
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _admin_only(current_user)
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role:
        u.role = RoleEnum(payload.role)
    if payload.is_email_verified is not None:
        u.is_email_verified = payload.is_email_verified
    db.add(AuditLog(user_id=current_user.id, action="update_user", entity_type="user", entity_id=u.id))
    db.commit()
    db.refresh(u)
    return u


@router.get("/moderation", response_model=list[dict])
def moderation_queue(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _admin_only(current_user)
    rows = (
        db.query(Problem)
        .filter(Problem.status.in_([ProblemStatusEnum.PENDING_VALIDATION, ProblemStatusEnum.DUPLICATE, ProblemStatusEnum.REJECTED]))
        .order_by(Problem.created_at.desc())
        .all()
    )
    return [
        {"id": p.id, "title": p.title, "status": p.status.value, "ai_category": p.ai_category, "ai_duplicate_of": p.ai_duplicate_of}
        for p in rows
    ]


@router.post("/problems/{problem_id}/status", response_model=dict)
def set_status(problem_id: str, payload: StatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _admin_only(current_user)
    p = db.get(Problem, problem_id)
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
    p.status = ProblemStatusEnum(payload.status)
    db.add(AuditLog(user_id=current_user.id, action="set_status", entity_type="problem", entity_id=p.id))
    db.commit()
    return {"ok": True, "status": p.status.value}


@router.get("/ai-config", response_model=dict)
def ai_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _admin_only(current_user)
    from app.core.config import settings
    return {
        "ai_enabled": settings.ai_enabled,
        "duplicate_threshold": settings.DUPLICATE_THRESHOLD,
        "email_configured": settings.email_configured,
    }


@router.post("/notifications/broadcast", status_code=status.HTTP_201_CREATED)
def broadcast(payload: BroadcastIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _admin_only(current_user)
    q = db.query(User)
    if payload.role:
        q = q.filter(User.role == RoleEnum(payload.role))
    users = q.all()
    for u in users:
        db.add(Notification(user_id=u.id, type=NotificationTypeEnum.GENERIC, message=payload.message))
    db.add(AuditLog(user_id=current_user.id, action="broadcast", entity_type="notification"))
    db.commit()
    return {"ok": True, "recipients": len(users)}
