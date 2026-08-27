from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.enums import RoleEnum
from app.models.problem import Problem
from app.models.user import User
from app.schemas.extra import AnalysisOut
from app.services.pipeline import run_analysis

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze/{problem_id}", response_model=AnalysisOut)
def analyze(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the full AI pipeline (categorize + prioritize + dedupe + route) on a problem."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.submitter_id != current_user.id and current_user.role not in [
        RoleEnum.ADMIN, RoleEnum.GOVERNMENT, RoleEnum.UNIVERSITY_ADMIN, RoleEnum.FACULTY
    ]:
        raise HTTPException(status_code=403, detail="Not authorized to analyze this problem")
    return run_analysis(db, problem)
