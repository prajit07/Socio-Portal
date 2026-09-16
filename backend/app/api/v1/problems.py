from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_user, require_role
from app.models.enums import RoleEnum, ProblemStatusEnum, ProblemPriorityEnum, SolutionStatusEnum
from app.models.problem import Problem, Solution
from app.models.user import User
from app.schemas.problem import (
    ProblemCreate,
    ProblemUpdate,
    ProblemOut,
    ProblemListOut,
    ProblemDelete,
    SolutionCreate,
    SolutionUpdate,
    SolutionOut,
    SolutionListOut,
)

router = APIRouter(prefix="/problems", tags=["problems"])


# ==================== Problem Endpoints ====================

@router.post("", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
def create_problem(
    problem_in: ProblemCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a new societal problem. Only citizens can submit problems."""
    if current_user.role != RoleEnum.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can submit problems"
        )

    problem = Problem(
        **problem_in.model_dump(),
        submitter_id=current_user.id,
        status=ProblemStatusEnum.PENDING_VALIDATION,
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    problem_id = problem.id

    def _run_in_background(pid: str):
        # Fresh session: request-scoped db is closed by the time this runs.
        from app.core.database import SessionLocal
        from app.models.problem import Problem as ProblemModel
        bg = SessionLocal()
        try:
            obj = bg.query(ProblemModel).filter(ProblemModel.id == pid).first()
            if obj is None:
                return
            from app.services.pipeline import run_analysis
            run_analysis(bg, obj)
        except Exception:
            bg.rollback()
        finally:
            bg.close()

    # AI pipeline (LLM + embedding + routing) takes seconds — don't block POST.
    background_tasks.add_task(_run_in_background, problem_id)
    return problem


@router.get("", response_model=List[ProblemListOut])
def list_problems(
    status: Optional[ProblemStatusEnum] = None,
    ai_category: Optional[str] = None,
    ai_priority: Optional[ProblemPriorityEnum] = None,
    submitter_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    mine_only: bool = Query(False, description="Citizens: only return my own reports"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """List problems with filters. Public — guests see all public problems.

    - Guests (no token): all non-deleted problems (for public map / homepage).
    - Citizens: all non-deleted by default; pass mine_only=true (or
      submitter_id=<own id>) to scope to just their own reports.
    - Industry: tag-matched subset (existing behaviour).
    - HEI / Gov / Admin: all.
    """
    from sqlalchemy.orm import defer

    query = db.query(Problem).filter(Problem.deleted_at.is_(None))
    # Don't pull the 384-dim pgvector per row for list views.
    if hasattr(Problem, "embedding") and Problem.embedding is not None:
        try:
            query = query.options(defer(Problem.embedding))
        except Exception:
            pass

    if current_user is None:
        # Public / guest access — no role filtering, just the explicit filters.
        pass
    elif current_user.role == RoleEnum.CITIZEN:
        # Citizens see the public feed by default (map / explorer).
        # Dashboard passes mine_only=true to keep the "My Problems" view.
        if mine_only:
            query = query.filter(Problem.submitter_id == current_user.id)
        elif submitter_id and submitter_id == current_user.id:
            query = query.filter(Problem.submitter_id == current_user.id)
    elif current_user.role in [RoleEnum.STUDENT, RoleEnum.FACULTY, RoleEnum.UNIVERSITY_ADMIN, RoleEnum.GOVERNMENT, RoleEnum.ADMIN]:
        # HEI / Gov / Admin see all problems (for browsing / oversight)
        pass
    elif current_user.role == RoleEnum.INDUSTRY:
        # Industry sees everything; UI can further filter by domain-tag match
        pass
    # Admin sees all
    
    # Apply filters
    if status:
        query = query.filter(Problem.status == status)
    if ai_category:
        query = query.filter(Problem.ai_category == ai_category)
    if ai_priority:
        query = query.filter(Problem.ai_priority == ai_priority)
    if submitter_id:
        query = query.filter(Problem.submitter_id == submitter_id)
    if assigned_to_id:
        query = query.filter(Problem.assigned_to_id == assigned_to_id)
    
    is_industry_filtered = (
        current_user is not None
        and current_user.role == RoleEnum.INDUSTRY
        and bool(set(current_user.domain_tags or []))
    )
    if is_industry_filtered and skip == 0:
        # Over-fetch a bounded pool, filter in Python (ai_tags is JSON),
        # then slice to the requested page size.
        pool = query.order_by(Problem.created_at.desc()).offset(0).limit(min(limit * 5, 500)).all()
        user_tags = set(current_user.domain_tags or [])
        return [p for p in pool if set(p.ai_tags or []) & user_tags][:limit]

    problems = query.order_by(Problem.created_at.desc()).offset(skip).limit(limit).all()

    # Industry with offset: filter the fetched page (best-effort).
    if is_industry_filtered:
        user_tags = set(current_user.domain_tags or [])
        problems = [p for p in problems if set(p.ai_tags or []) & user_tags]
    return problems


@router.get("/{problem_id}", response_model=ProblemOut)
def get_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get a specific problem by ID. Public so guests can open map pins."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if problem.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Problem not found")

    return problem


@router.patch("/{problem_id}", response_model=ProblemOut)
def update_problem(
    problem_id: str,
    problem_in: ProblemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a problem. Only submitter or admins/HEI can update."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Check permissions
    can_update = (
        problem.submitter_id == current_user.id or
        current_user.role in [RoleEnum.ADMIN, RoleEnum.GOVERNMENT, RoleEnum.UNIVERSITY_ADMIN, RoleEnum.FACULTY]
    )
    if not can_update:
        raise HTTPException(status_code=403, detail="Not authorized to update this problem")
    
    update_data = problem_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(problem, field, value)
    
    db.commit()
    db.refresh(problem)
    return problem


@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(
    problem_id: str,
    payload: ProblemDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a problem. Only the submitter (with a reason) or an admin can remove it.

    We soft-delete (record deleted_at + reason) rather than hard-deleting so that
    linked solutions / teams / comments are preserved and the removal is auditable.
    """
    from datetime import datetime, timezone

    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem or problem.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Problem not found")

    if problem.submitter_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this problem")

    problem.deleted_at = datetime.now(timezone.utc)
    problem.deletion_reason = payload.reason
    problem.deleted_by_id = current_user.id
    db.commit()


# ==================== Solution Endpoints ====================

@router.post("/{problem_id}/solutions", response_model=SolutionOut, status_code=status.HTTP_201_CREATED)
def create_solution(
    problem_id: str,
    solution_in: SolutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a solution to a problem. Solvers (students, faculty, industry) can submit."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Check if user can submit solution
    solver_roles = [RoleEnum.STUDENT, RoleEnum.FACULTY, RoleEnum.INDUSTRY, RoleEnum.UNIVERSITY_ADMIN]
    if current_user.role not in solver_roles and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only solvers (students, faculty, industry) can submit solutions"
        )
    
    solution = Solution(
        **solution_in.model_dump(),
        problem_id=problem_id,
        author_id=current_user.id,
        status=SolutionStatusEnum.DRAFT,
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)
    return solution


@router.get("/{problem_id}/solutions", response_model=List[SolutionListOut])
def list_solutions(
    problem_id: str,
    status: Optional[SolutionStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List solutions for a problem."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    query = db.query(Solution).filter(Solution.problem_id == problem_id)
    
    if status:
        query = query.filter(Solution.status == status)
    
    solutions = query.order_by(Solution.created_at.desc()).offset(skip).limit(limit).all()
    return solutions


@router.get("/{problem_id}/solutions/{solution_id}", response_model=SolutionOut)
def get_solution(
    problem_id: str,
    solution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific solution."""
    solution = db.query(Solution).filter(
        Solution.id == solution_id,
        Solution.problem_id == problem_id
    ).first()
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    
    return solution


@router.patch("/{problem_id}/solutions/{solution_id}", response_model=SolutionOut)
def update_solution(
    problem_id: str,
    solution_id: str,
    solution_in: SolutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a solution. Only author or admins/HEI."""
    solution = db.query(Solution).filter(
        Solution.id == solution_id,
        Solution.problem_id == problem_id
    ).first()
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    
    can_update = (
        solution.author_id == current_user.id or
        current_user.role in [RoleEnum.ADMIN, RoleEnum.GOVERNMENT, RoleEnum.UNIVERSITY_ADMIN, RoleEnum.FACULTY]
    )
    if not can_update:
        raise HTTPException(status_code=403, detail="Not authorized to update this solution")
    
    update_data = solution_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(solution, field, value)
    
    db.commit()
    db.refresh(solution)
    return solution