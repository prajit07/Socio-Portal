from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.engagement import Comment, Upvote

router = APIRouter(prefix="/engagement", tags=["engagement"])


class CommentIn(BaseModel):
    entity_type: str
    entity_id: str
    content: str


@router.post("/comments", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_comment(payload: CommentIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = Comment(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        user_id=current_user.id,
        content=payload.content,
    )
    db.add(c)
    db.commit()
    return {"ok": True, "id": c.id}


@router.get("/comments", response_model=list[dict])
def list_comments(entity_type: str, entity_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Comment, User.name)
        .join(User, User.id == Comment.user_id)
        .filter(Comment.entity_type == entity_type, Comment.entity_id == entity_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return [
        {"id": c.id, "user_id": c.user_id, "name": u.name, "content": c.content, "created_at": c.created_at}
        for c, u in rows
    ]


class UpvoteIn(BaseModel):
    problem_id: str


@router.post("/upvotes", response_model=dict)
def toggle_upvote(payload: UpvoteIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = (
        db.query(Upvote)
        .filter(Upvote.problem_id == payload.problem_id, Upvote.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        upvoted = False
    else:
        db.add(Upvote(problem_id=payload.problem_id, user_id=current_user.id))
        db.commit()
        upvoted = True
    count = db.query(func.count(Upvote.id)).filter(Upvote.problem_id == payload.problem_id).scalar() or 0
    return {"upvoted": upvoted, "count": count}


@router.get("/upvotes", response_model=dict)
def upvote_count(problem_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = db.query(func.count(Upvote.id)).filter(Upvote.problem_id == problem_id).scalar() or 0
    mine = (
        db.query(Upvote)
        .filter(Upvote.problem_id == problem_id, Upvote.user_id == current_user.id)
        .first()
    )
    return {"count": count, "upvoted": bool(mine)}
