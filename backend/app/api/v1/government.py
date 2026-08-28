from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.problem import Problem
from app.models.org import University, Industry
from app.models.problem import Solution
from app.models.collaboration import Collaboration

router = APIRouter(prefix="/government", tags=["government"])


@router.get("/analytics", response_model=dict)
def analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.value not in ("government", "admin"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=403, detail="Government access only")

    total = db.query(func.count(Problem.id)).scalar() or 0
    by_status = (
        db.query(Problem.status, func.count(Problem.id))
        .group_by(Problem.status)
        .all()
    )
    by_category = (
        db.query(Problem.ai_category, func.count(Problem.id))
        .filter(Problem.ai_category.isnot(None))
        .group_by(Problem.ai_category)
        .all()
    )
    by_priority = (
        db.query(Problem.ai_priority, func.count(Problem.id))
        .filter(Problem.ai_priority.isnot(None))
        .group_by(Problem.ai_priority)
        .all()
    )
    active_collab = db.query(func.count(Collaboration.id)).scalar() or 0
    proposals = db.query(func.count(Solution.id)).scalar() or 0
    universities = db.query(func.count(University.id)).scalar() or 0
    industries = db.query(func.count(Industry.id)).scalar() or 0

    def cnt(statuses):
        return sum(c for s, c in by_status if s.value in statuses) if by_status else 0

    resolved = cnt({"implemented", "closed"})
    open_count = cnt({"open", "validated", "in_review", "proposal_submitted"})

    return {
        "kpis": {
            "total_problems": total,
            "resolved": resolved,
            "open": open_count,
            "active_collaborations": active_collab,
            "proposals": proposals,
            "universities": universities,
            "industries": industries,
        },
        "by_status": [{"status": s.value, "count": c} for s, c in by_status],
        "by_category": [{"category": cat, "count": c} for cat, c in by_category],
        "by_priority": [{"priority": (p.value if p else "none"), "count": c} for p, c in by_priority],
    }


@router.get("/leaderboards", response_model=dict)
def leaderboards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.value not in ("government", "admin"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=403, detail="Government access only")

    unis = db.query(University.id, University.name, University.verified).order_by(University.name).all()
    inds = db.query(Industry.id, Industry.name, Industry.verified).order_by(Industry.name).all()
    return {
        "universities": [{"id": u.id, "name": u.name, "verified": u.verified} for u in unis],
        "industries": [{"id": i.id, "name": i.name, "verified": i.verified} for i in inds],
    }
