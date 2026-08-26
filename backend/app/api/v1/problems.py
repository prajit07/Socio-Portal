from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.enums import RoleEnum, ProblemStatusEnum, ProblemPriorityEnum
from app.models.problem import Problem, Solution
from app.models.user import User
from app.schemas.problem import (
    ProblemCreate,
    ProblemUpdate,
    ProblemOut,
    ProblemListOut,
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
        status=ProblemStatusEnum.SUBMITTED,
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


@router.get("", response_model=List[ProblemListOut])
def list_problems(
    status: Optional[ProblemStatusEnum] = None,
    ai_category: Optional[str] = None,
    ai_priority: Optional[ProblemPriorityEnum] = None,
    submitter_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List problems with filters. Access depends on role."""
    query = db.query(Problem)
    
    # Role-based filtering
    if current_user.role == RoleEnum.CITIZEN:
        # Citizens see only their own problems
        query = query.filter(Problem.submitter_id == current_user.id)
    elif current_user.role in [RoleEnum.STUDENT, RoleEnum.FACULTY, RoleEnum.UNIVERSITY_ADMIN]:
        # HEI users see all problems (for browsing/selection)
        pass
    elif current_user.role == RoleEnum.INDUSTRY:
        # Industry sees problems assigned to them or all for browsing
        pass
    elif current_user.role == RoleEnum.GOVERNMENT:
        # Government sees all problems
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
    
    problems = query.order_by(Problem.created_at.desc()).offset(skip).limit(limit).all()
    return problems


@router.get("/{problem_id}", response_model=ProblemOut)
def get_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific problem by ID."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Check access permissions
    if current_user.role == RoleEnum.CITIZEN and problem.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this problem")
    
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a problem. Only submitter or admin."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    if problem.submitter_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this problem")
    
    db.delete(problem)
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


# ==================== AI Categorization Endpoint (Mock) ====================

@router.post("/{problem_id}/categorize", response_model=ProblemOut)
def categorize_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.GOVERNMENT, RoleEnum.UNIVERSITY_ADMIN, RoleEnum.FACULTY)),
):
    """AI categorization of problem (mock implementation)."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Mock AI categorization based on tags/description
    # In production, this would call an LLM API
    mock_categories = {
        "waste": "Waste Management",
        "water": "Water & Sanitation",
        "traffic": "Transportation",
        "education": "Education",
        "health": "Healthcare",
        "energy": "Energy & Environment",
        "agriculture": "Agriculture",
        "housing": "Housing & Urban Development",
    }
    
    text = (problem.description + " " + (problem.evidence_text or "") + " " + " ".join(problem.tags or [])).lower()
    
    ai_category = "General"
    for keyword, category in mock_categories.items():
        if keyword in text:
            ai_category = category
            break
    
    ai_tags = []
    for keyword in mock_categories.keys():
        if keyword in text:
            ai_tags.append(keyword)
    
    # Priority based on keywords
    priority = ProblemPriorityEnum.MEDIUM
    if any(w in text for w in ["urgent", "critical", "emergency", "dangerous", "hazard"]):
        priority = ProblemPriorityEnum.HIGH
    if any(w in text for w in ["life threatening", "disaster", "catastrophe"]):
        priority = ProblemPriorityEnum.CRITICAL
    
    problem.ai_category = ai_category
    problem.ai_tags = ai_tags
    problem.ai_priority = priority
    problem.status = ProblemStatusEnum.CATEGORIZED
    
    db.commit()
    db.refresh(problem)
    return problem