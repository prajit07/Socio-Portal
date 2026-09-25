from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.org import UniversityMember
from app.models.problem import Problem
from app.models.enums import NotificationTypeEnum
from app.schemas.team import TeamCreate, TeamOut, AddMemberIn, TeamMemberOut
from app.services.notification_service import create_notification

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
    # A team belongs to the creator's own institute. Students/faculty must be
    # linked to an institute to form a team; admins may attach any institute.
    if current_user.role.value == "admin":
        university_id = payload.university_id
        if not university_id:
            raise HTTPException(status_code=400, detail="Institute is required")
    elif current_user.role.value == "university_admin":
        mine = (
            db.query(UniversityMember.university_id)
            .filter(
                UniversityMember.user_id == current_user.id,
                UniversityMember.member_role == "admin",
            )
            .all()
        )
        owned = {u[0] for u in mine}
        if payload.university_id and payload.university_id not in owned:
            raise HTTPException(status_code=403, detail="You can only form teams for your own institute")
        if not owned:
            raise HTTPException(status_code=403, detail="Register your institute first")
        university_id = payload.university_id or next(iter(owned))
    else:
        # student / faculty — team must be attached to an institute they are a
        # member of, matching the member's own institute requirement.
        mine = (
            db.query(UniversityMember.university_id)
            .filter(UniversityMember.user_id == current_user.id)
            .all()
        )
        membership = {u[0] for u in mine}
        if not membership:
            raise HTTPException(status_code=403, detail="You aren't linked to any institute yet. Link your institute to form a team.")
        if payload.university_id and payload.university_id not in membership:
            raise HTTPException(status_code=403, detail="You can only form teams for an institute you belong to")
        university_id = payload.university_id or next(iter(membership))
    team = Team(
        problem_id=payload.problem_id,
        name=payload.name,
        university_id=university_id,
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
        db.query(TeamMember, User)
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
        "members": [{"id": m.id, "user_id": u.id, "name": u.name, "email": u.email, "role": m.role} for m, u in members],
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
    if current_user.role.value == "admin":
        pass
    elif team.created_by == current_user.id:
        pass
    else:
        is_member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )
        if not is_member:
            raise HTTPException(status_code=403, detail="Only team members can add collaborators")
    if payload.user_id:
        target = db.get(User, payload.user_id)
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
    elif payload.email:
        target = (
            db.query(User)
            .filter(User.email.ilike(payload.email.strip().lower()))
            .first()
        )
        if not target:
            raise HTTPException(status_code=404, detail="No registered user with that email")
    else:
        raise HTTPException(status_code=422, detail="Provide user_id or email")
    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == target.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already a team member")
    member = TeamMember(team_id=team_id, user_id=target.id, role=payload.role or "member")
    db.add(member)
    create_notification(
        db,
        user_id=target.id,
        message=f"You were added to team '{team.name}'.",
        notif_type=NotificationTypeEnum.GENERIC,
        reference_id=team_id,
    )
    db.commit()
    db.refresh(member)
    return member
