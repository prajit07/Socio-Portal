from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.problem import Problem
from app.schemas.team import TeamCreate, TeamOut, AddMemberIn, TeamMemberOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    solver_roles = ("student", "faculty", "university_admin", "admin")
    if current_user.role.value not in solver_roles:
        raise HTTPException(status_code=403, detail="Only university members can form teams")
    problem = db.get(Problem, payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    team = Team(
        problem_id=payload.problem_id,
        name=payload.name,
        university_id=payload.university_id,
        created_by=current_user.id,
    )
    db.add(team)
    db.flush()
    # creator is a member
    db.add(TeamMember(team_id=team.id, user_id=current_user.id, role="lead"))
    for uid in payload.member_ids or []:
        db.add(TeamMember(team_id=team.id, user_id=uid))
    db.commit()
    db.refresh(team)
    return team


@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Team)
    if current_user.role.value in ("student", "faculty"):
        q = q.filter(
            (Team.created_by == current_user.id)
            | (Team.id.in_(db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user.id)))
        )
    return q.order_by(Team.created_at.desc()).all()


@router.get("/{team_id}", response_model=dict)
def get_team(team_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = (
        db.query(TeamMember, User.name, User.email)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
        .all()
    )
    return {
        "id": team.id,
        "problem_id": team.problem_id,
        "university_id": team.university_id,
        "name": team.name,
        "created_by": team.created_by,
        "created_at": team.created_at,
        "members": [{"id": m.id, "user_id": u.id, "name": u.name, "email": u.email, "role": m.role} for m, u, _ in members],
    }


@router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    team_id: str,
    payload: AddMemberIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    member = TeamMember(team_id=team_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
