from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.enums import RoleEnum, ProblemStatusEnum, SolutionStatusEnum
from app.models.problem import Problem, Solution
from app.models.user import User
from app.models.team import Team, TeamMember
from app.schemas.problem import SolutionOut, SolutionListOut

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ProposalCreate(BaseModel):
    team_id: str
    problem_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    estimated_budget: Optional[str] = None
    estimated_timeline: Optional[str] = None
    document_urls: Optional[List[str]] = None


class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    estimated_budget: Optional[str] = None
    estimated_timeline: Optional[str] = None
    document_urls: Optional[List[str]] = None


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
    db.commit()
    db.refresh(proposal)
    return proposal
