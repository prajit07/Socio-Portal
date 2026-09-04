"""Classification Feedback API — Active Learning Collection.

Allows users to correct AI classifications. Corrections are stored and used to:
1. Track classification accuracy per category
2. Regenerate few-shot examples with real corrections
3. Future: fine-tune a dedicated classifier when enough data collected
"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.problem import Problem
from app.models.classification_feedback import ClassificationFeedback, ClassificationMetrics
from app.schemas.problem import ProblemOut

router = APIRouter(prefix="/classification", tags=["classification"])


class FeedbackIn(BaseModel):
    """User correction to AI classification."""
    problem_id: str = Field(..., min_length=1)
    # User provides the correct classification
    corrected_category_id: str = Field(..., min_length=1)
    corrected_category_name: str = Field(..., min_length=1)
    corrected_tags: Optional[List[str]] = None
    corrected_priority: Optional[str] = None
    notes: Optional[str] = None


class FeedbackOut(BaseModel):
    id: str
    problem_id: str
    ai_category_id: Optional[str]
    ai_category_name: Optional[str]
    corrected_category_id: str
    corrected_category_name: str
    is_correction: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MetricsOut(BaseModel):
    category_id: str
    category_name: str
    total_predictions: int
    correct_predictions: int
    user_corrections: int
    accuracy: float
    priority_accuracy: Optional[dict] = None

    class Config:
        from_attributes = True


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback: FeedbackIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a correction to AI classification.
    
    If the AI prediction matches user's correction, is_correction=False.
    This tracks accuracy automatically.
    """
    problem = db.query(Problem).filter(Problem.id == feedback.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Determine if this is a correction (user disagreed with AI)
    ai_category = problem.ai_category
    ai_category_id = None
    # Map category name back to ID if needed
    from app.ml import NAME_TO_ID
    if ai_category and ai_category in NAME_TO_ID:
        ai_category_id = NAME_TO_ID[ai_category]

    is_correction = (
        ai_category_id != feedback.corrected_category_id or
        (problem.ai_priority and problem.ai_priority.value != feedback.corrected_priority)
    )

    fb = ClassificationFeedback(
        problem_id=feedback.problem_id,
        ai_category_id=ai_category_id,
        ai_category_name=ai_category,
        ai_tags=problem.ai_tags,
        ai_priority=problem.ai_priority.value if problem.ai_priority else None,
        corrected_category_id=feedback.corrected_category_id,
        corrected_category_name=feedback.corrected_category_name,
        corrected_tags=feedback.corrected_tags,
        corrected_priority=feedback.corrected_priority,
        user_id=current_user.id,
        is_correction=is_correction,
        notes=feedback.notes,
    )
    db.add(fb)

    # Update metrics
    _update_metrics(db, feedback.corrected_category_id, feedback.corrected_category_name, is_correction)

    db.commit()
    db.refresh(fb)
    return fb


@router.get("/feedback/{problem_id}", response_model=List[FeedbackOut])
def get_feedback(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all feedback for a problem."""
    return db.query(ClassificationFeedback).filter(
        ClassificationFeedback.problem_id == problem_id
    ).order_by(ClassificationFeedback.created_at.desc()).all()


@router.get("/metrics", response_model=List[MetricsOut])
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get classification accuracy metrics per category (admin/government)."""
    if current_user.role.value not in ("admin", "government"):
        raise HTTPException(status_code=403, detail="Admin/government access only")
    
    metrics = db.query(ClassificationMetrics).order_by(
        ClassificationMetrics.total_predictions.desc()
    ).all()
    return metrics


@router.post("/regenerate-few-shot")
def regenerate_few_shot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regenerate few-shot examples using real user corrections.
    
    Admin only. Combines synthetic examples with high-confidence real corrections.
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    from app.ml.synthetic_data_generator import generate_few_shot_examples, save_few_shot_examples

    # Get high-quality corrections (where user corrected AI)
    corrections = db.query(ClassificationFeedback).filter(
        ClassificationFeedback.is_correction == True
    ).all()

    # Convert corrections to few-shot format
    real_examples = []
    for c in corrections:
        # Get the original problem for context
        problem = db.get(Problem, c.problem_id)
        if problem:
            real_examples.append({
                "title": problem.title,
                "description": problem.description,
                "transcript": problem.evidence_text or "",
                "user_tags": problem.tags or [],
                "category_id": c.corrected_category_id,
                "category_name": c.corrected_category_name,
                "tags": [
                    {"id": c.corrected_category_id, "name": c.corrected_category_name, "confidence": 1.0}
                ] + [
                    {"id": t.replace(" ", "_"), "name": t, "confidence": 0.9}
                    for t in (c.corrected_tags or [])
                ],
                "priority": c.corrected_priority or "medium",
            })

    # Generate fresh synthetic + add real corrections
    synthetic = generate_few_shot_examples(examples_per_category=2)
    all_examples = synthetic + real_examples

    # Save combined
    output_path = os.path.join(os.path.dirname(__file__), "..", "ml", "few_shot_examples.json")
    save_few_shot_examples(all_examples, output_path)

    # Reload in memory
    from app.services.ai_categorization import _load_few_shot_examples
    import app.services.ai_categorization as ac
    ac._FEW_SHOT_EXAMPLES = _load_few_shot_examples(max_per_category=2)

    return {
        "detail": "Few-shot examples regenerated",
        "synthetic_count": len(synthetic),
        "real_corrections_count": len(real_examples),
        "total": len(all_examples)
    }


def _update_metrics(db: Session, category_id: str, category_name: str, is_correction: bool):
    """Update classification metrics atomically."""
    metric = db.query(ClassificationMetrics).filter(
        ClassificationMetrics.category_id == category_id
    ).first()
    if not metric:
        metric = ClassificationMetrics(category_id=category_id, category_name=category_name)
        db.add(metric)
    
    metric.total_predictions += 1
    if not is_correction:
        metric.correct_predictions += 1
    else:
        metric.user_corrections += 1
    db.flush()


import os