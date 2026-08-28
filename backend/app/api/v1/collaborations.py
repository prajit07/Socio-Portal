from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.collaboration import Collaboration, Milestone, Deliverable, IPRecord, SocialImpactReport
from app.models.problem import Solution, Problem
from app.models.org import Industry
from app.models.routing import Notification
from app.models.enums import ProblemStatusEnum, NotificationTypeEnum
from app.schemas.collaboration import (
    CollaborationCreate,
    CollaborationUpdate,
    CollaborationOut,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneOut,
    DeliverableIn,
    DeliverableOut,
    IPRecordIn,
    IPRecordOut,
    ImpactReportIn,
    ImpactReportOut,
)

router = APIRouter(prefix="/collaborations", tags=["collaborations"])

STAGE_TO_STATUS = {
    "interested": ProblemStatusEnum.IN_COLLABORATION,
    "funding": ProblemStatusEnum.IN_COLLABORATION,
    "prototype": ProblemStatusEnum.PROTOTYPE,
    "pilot": ProblemStatusEnum.PILOT,
    "implementation": ProblemStatusEnum.IMPLEMENTED,
    "impact_logged": ProblemStatusEnum.CLOSED,
}


def _notify(db, user_id, message, ref=None):
    db.add(Notification(user_id=user_id, type=NotificationTypeEnum.GENERIC, message=message, reference_id=ref))


@router.post("", response_model=CollaborationOut, status_code=status.HTTP_201_CREATED)
def express_interest(
    payload: CollaborationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.value not in ("industry", "admin"):
        raise HTTPException(status_code=403, detail="Only industry partners can start collaborations")
    proposal = db.get(Solution, payload.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    ind = db.get(Industry, payload.industry_id)
    if not ind:
        raise HTTPException(status_code=404, detail="Industry not found")
    collab = Collaboration(
        proposal_id=payload.proposal_id,
        industry_id=payload.industry_id,
        stage=payload.stage,
        notes=payload.notes,
    )
    db.add(collab)
    db.flush()
    problem = db.get(Problem, proposal.problem_id)
    if problem:
        problem.status = ProblemStatusEnum.IN_COLLABORATION
    _notify(db, proposal.author_id, f"Industry '{ind.name}' expressed interest in your proposal '{proposal.title}'.", proposal.id)
    db.commit()
    db.refresh(collab)
    return collab


@router.get("", response_model=list[CollaborationOut])
def list_collaborations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Industry partners see their collaborations; admins/gov see all; citizens see
    collaborations on problems they submitted."""
    if current_user.role.value == "citizen":
        problem_ids = db.query(Problem.id).filter(Problem.submitter_id == current_user.id)
        proposal_ids = db.query(Solution.id).filter(Solution.problem_id.in_(problem_ids))
        return (
            db.query(Collaboration)
            .filter(Collaboration.proposal_id.in_(proposal_ids))
            .order_by(Collaboration.started_at.desc())
            .all()
        )
    return db.query(Collaboration).order_by(Collaboration.started_at.desc()).all()


@router.get("/{collaboration_id}", response_model=dict)
def get_collaboration(collaboration_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.get(Collaboration, collaboration_id)
    if not c:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    return {
        "id": c.id,
        "proposal_id": c.proposal_id,
        "industry_id": c.industry_id,
        "stage": c.stage,
        "notes": c.notes,
        "started_at": c.started_at,
        "updated_at": c.updated_at,
        "milestones": [
            {"id": m.id, "title": m.title, "status": m.status, "due_date": m.due_date, "completed_at": m.completed_at, "description": m.description}
            for m in c.milestones
        ],
        "ip_records": [{"id": i.id, "type": i.type, "status": i.status, "reference_no": i.reference_no} for i in c.ip_records],
        "impact_reports": [
            {"id": r.id, "beneficiaries_count": r.beneficiaries_count, "impact_summary": r.impact_summary, "district": r.district, "state": r.state}
            for r in c.impact_reports
        ],
    }


@router.patch("/{collaboration_id}", response_model=CollaborationOut)
def update_collaboration(
    collaboration_id: str,
    payload: CollaborationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = db.get(Collaboration, collaboration_id)
    if not c:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    if current_user.role.value not in ("industry", "admin"):
        raise HTTPException(status_code=403, detail="Not permitted")
    data = payload.model_dump(exclude_unset=True)
    if data.get("stage"):
        c.stage = data["stage"]
        problem = db.query(Problem).join(Solution, Solution.problem_id == Problem.id).filter(Solution.id == c.proposal_id).first()
        if problem and data["stage"] in STAGE_TO_STATUS:
            problem.status = STAGE_TO_STATUS[data["stage"]]
    if data.get("notes") is not None:
        c.notes = data["notes"]
    db.commit()
    db.refresh(c)
    return c


@router.post("/{collaboration_id}/milestones", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def add_milestone(collaboration_id: str, payload: MilestoneCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.get(Collaboration, collaboration_id)
    if not c:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    m = Milestone(collaboration_id=collaboration_id, **payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.patch("/{collaboration_id}/milestones/{milestone_id}", response_model=MilestoneOut)
def update_milestone(collaboration_id: str, milestone_id: str, payload: MilestoneUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    m = db.get(Milestone, milestone_id)
    if not m or m.collaboration_id != collaboration_id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m


@router.post("/{collaboration_id}/deliverables", response_model=DeliverableOut, status_code=status.HTTP_201_CREATED)
def add_deliverable(collaboration_id: str, milestone_id: str, payload: DeliverableIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    m = db.get(Milestone, milestone_id)
    if not m or m.collaboration_id != collaboration_id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    d = Deliverable(milestone_id=milestone_id, **payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.post("/{collaboration_id}/ip", response_model=IPRecordOut, status_code=status.HTTP_201_CREATED)
def add_ip(collaboration_id: str, payload: IPRecordIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.get(Collaboration, collaboration_id)
    if not c:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    ip = IPRecord(collaboration_id=collaboration_id, **payload.model_dump())
    db.add(ip)
    db.commit()
    db.refresh(ip)
    return ip


@router.post("/{collaboration_id}/impact", response_model=ImpactReportOut, status_code=status.HTTP_201_CREATED)
def add_impact(collaboration_id: str, payload: ImpactReportIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.get(Collaboration, collaboration_id)
    if not c:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    r = SocialImpactReport(collaboration_id=collaboration_id, **payload.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r
