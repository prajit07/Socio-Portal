from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.org import Industry
from app.models.problem import Solution
from app.schemas.org import IndustryCreate, IndustryOut
from app.models.enums import SolutionStatusEnum

router = APIRouter(prefix="/industries", tags=["industries"])


class IndustryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    domain_tags: Optional[List[str]] = None
    verified: Optional[bool] = None


@router.post("", response_model=IndustryOut, status_code=status.HTTP_201_CREATED)
def create_industry(
    payload: IndustryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in ("admin", "industry"):
        raise HTTPException(status_code=403, detail="Only admin or industry can create industry profiles")
    ind = Industry(**payload.model_dump())
    db.add(ind)
    db.commit()
    db.refresh(ind)
    return ind


@router.get("", response_model=list[IndustryOut])
def list_industries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Industry).order_by(Industry.name).all()


@router.get("/{industry_id}", response_model=IndustryOut)
def get_industry(industry_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ind = db.get(Industry, industry_id)
    if not ind:
        raise HTTPException(status_code=404, detail="Industry not found")
    return ind


@router.patch("/{industry_id}", response_model=IndustryOut)
def update_industry(
    industry_id: str,
    payload: IndustryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ind = db.get(Industry, industry_id)
    if not ind:
        raise HTTPException(status_code=404, detail="Industry not found")
    if current_user.role.value not in ("admin", "industry"):
        raise HTTPException(status_code=403, detail="Not permitted")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ind, k, v)
    db.commit()
    db.refresh(ind)
    return ind


@router.get("/{industry_id}/proposals", response_model=list[dict])
def industry_proposals(industry_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Posted solution proposals (submitted/accepted) for an industry to pick up."""
    ind = db.get(Industry, industry_id)
    if not ind:
        raise HTTPException(status_code=404, detail="Industry not found")
    proposals = (
        db.query(Solution)
        .filter(Solution.status.in_([SolutionStatusEnum.SUBMITTED, SolutionStatusEnum.ACCEPTED]))
        .order_by(Solution.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "team_id": p.team_id,
            "problem_id": p.problem_id,
            "title": p.title,
            "description": p.description,
            "status": p.status.value if isinstance(p.status, SolutionStatusEnum) else p.status,
            "budget_estimate": p.estimated_budget,
            "timeline_estimate": p.estimated_timeline,
        }
        for p in proposals
    ]
