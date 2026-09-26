from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Union
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.enums import (
    RoleEnum,
    ProblemStatusEnum,
    SolutionStatusEnum,
    NotificationTypeEnum,
)
from app.models.problem import Problem, Solution
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.org import Industry, UniversityMember
from app.schemas.problem import SolutionOut, SolutionListOut
from app.services.notification_service import create_notification

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ProposalCreate(BaseModel):
    team_id: str
    problem_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    estimated_budget: Optional[Union[str, int, float]] = None
    estimated_timeline: Optional[str] = None
    document_urls: Optional[List[str]] = None

    @field_validator("estimated_budget", mode="before")
    @classmethod
    def coerce_budget(cls, v):
        if v is None or isinstance(v, str):
            return v
        return str(int(v)) if isinstance(v, bool) is False and float(v).is_integer() else str(v)


class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    estimated_budget: Optional[Union[str, int, float]] = None
    estimated_timeline: Optional[str] = None
    document_urls: Optional[List[str]] = None

    @field_validator("estimated_budget", mode="before")
    @classmethod
    def coerce_budget(cls, v):
        if v is None or isinstance(v, str):
            return v
        return str(int(v)) if isinstance(v, bool) is False and float(v).is_integer() else str(v)


@router.post("", response_model=SolutionOut, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    solver_roles = ("student", "faculty", "university_admin", "industry", "admin")
    if current_user.role.value not in solver_roles:
        raise HTTPException(status_code=403, detail="Only solvers can submit proposals")
    problem = db.get(Problem, payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    team = db.get(Team, payload.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    proposal = Solution(
        team_id=payload.team_id,
        problem_id=payload.problem_id,
        title=payload.title,
        description=payload.description,
        estimated_budget=payload.estimated_budget,
        estimated_timeline=payload.estimated_timeline,
        document_urls=payload.document_urls,
        author_id=current_user.id,
        status=SolutionStatusEnum.DRAFT,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("", response_model=List[SolutionListOut])
def list_proposals(
    problem_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Solution)
    if problem_id:
        q = q.filter(Solution.problem_id == problem_id)
    if status:
        q = q.filter(Solution.status == status)
    if current_user.role.value in ("student", "faculty"):
        team_ids = db.query(Team.id).filter(
            (Team.created_by == current_user.id)
            | (Team.id.in_(db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user.id)))
        ).all()
        team_ids = [t[0] for t in team_ids]
        q = q.filter(Solution.team_id.in_(team_ids)) if team_ids else q.filter(False)
    elif current_user.role.value == "university_admin":
        # University admin scopes to proposals from teams of their own institutes.
        owned_unis = db.query(UniversityMember.university_id).filter(
            UniversityMember.user_id == current_user.id,
            UniversityMember.member_role == "admin",
        ).all()
        owned = {u[0] for u in owned_unis}
        team_ids = (
            db.query(Team.id).filter(Team.university_id.in_(owned)).all()
            if owned
            else db.query(Team.id).filter(False).all()
        )
        team_ids = [t[0] for t in team_ids]
        q = q.filter(Solution.team_id.in_(team_ids)) if team_ids else q.filter(False)
    return q.order_by(Solution.created_at.desc()).all()


@router.get("/{proposal_id}", response_model=SolutionOut)
def get_proposal(proposal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proposal = db.get(Solution, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.patch("/{proposal_id}", response_model=SolutionOut)
def update_proposal(
    proposal_id: str,
    payload: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    proposal = db.get(Solution, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.author_id != current_user.id and current_user.role.value not in ("faculty", "admin", "university_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(proposal, k, v)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.post("/{proposal_id}/submit", response_model=SolutionOut)
def submit_proposal(proposal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proposal = db.get(Solution, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.author_id != current_user.id and current_user.role.value not in ("faculty", "admin", "university_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    proposal.status = SolutionStatusEnum.SUBMITTED
    problem = db.get(Problem, proposal.problem_id)
    if problem:
        problem.status = ProblemStatusEnum.PROPOSAL_SUBMITTED
    db.commit()
    db.refresh(proposal)
    return proposal


@router.post("/{proposal_id}/approve", response_model=SolutionOut)
def approve_proposal(proposal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.value not in ("faculty", "admin", "university_admin"):
        raise HTTPException(status_code=403, detail="Only faculty/mentors can approve proposals")
    proposal = db.get(Solution, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal.status = SolutionStatusEnum.ACCEPTED
    proposal.approved_by = current_user.id
    proposal.approved_at = datetime.now(timezone.utc)
    try:
        create_notification(
            db,
            user_id=proposal.author_id,
            message="Your proposal has been approved by your institute.",
            notif_type=NotificationTypeEnum.STATUS_UPDATED,
            reference_id=proposal.id,
        )
    except Exception:
        pass
    db.commit()
    db.refresh(proposal)
    return proposal


class ProposalForward(BaseModel):
    industry_id: Optional[str] = None


@router.post("/{proposal_id}/forward", response_model=SolutionOut)
def forward_proposal(
    proposal_id: str,
    payload: ProposalForward,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in ("faculty", "admin", "university_admin"):
        raise HTTPException(status_code=403, detail="Only university admins, faculty or admins can forward proposals")
    proposal = db.get(Solution, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status not in (SolutionStatusEnum.SUBMITTED, SolutionStatusEnum.ACCEPTED):
        raise HTTPException(status_code=400, detail="Only submitted or approved proposals can be forwarded to industries")
    if payload.industry_id:
        industry = db.get(Industry, payload.industry_id)
        if not industry:
            raise HTTPException(status_code=404, detail="Industry not found")
        proposal.forwarded_to_industry_id = industry.id
    proposal.forwarded_by = current_user.id
    proposal.forwarded_at = datetime.now(timezone.utc)
    proposal.status = SolutionStatusEnum.FORWARDED
    # Notify industry partner and the student team.
    try:
        if payload.industry_id:
            industry = db.get(Industry, payload.industry_id)
            owner = db.get(User, industry.created_by) if industry and industry.created_by else None
            if owner and owner.role.value == "industry":
                create_notification(
                    db,
                    user_id=owner.id,
                    message=f"New proposal forwarded to you by an institute.",
                    notif_type=NotificationTypeEnum.PROPOSAL_RECEIVED,
                    reference_id=proposal.id,
                )
        create_notification(
            db,
            user_id=proposal.author_id,
            message="Your proposal has been forwarded to industry partners.",
            notif_type=NotificationTypeEnum.STATUS_UPDATED,
            reference_id=proposal.id,
        )
    except Exception:
        pass
    db.commit()
    db.refresh(proposal)
    return proposal
