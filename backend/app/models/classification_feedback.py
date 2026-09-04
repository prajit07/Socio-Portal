"""Classification Feedback model for active learning.

Stores user corrections to AI classifications. Used to:
1. Track classification accuracy
2. Regenerate few-shot examples with real corrections
3. Fine-tune/replace model when enough data collected
"""
import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, String, func, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ProblemStatusEnum


def generate_feedback_id() -> str:
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(10))
    return f"fb_{random_part}"


class ClassificationFeedback(Base):
    """User corrections to AI problem classification."""

    __tablename__ = "classification_feedback"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=generate_feedback_id
    )
    problem_id: Mapped[str] = mapped_column(String(20), ForeignKey("problems.id"), nullable=False, index=True)
    
    # What the AI predicted
    ai_category_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    ai_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # What the user corrected to (ground truth)
    corrected_category_id: Mapped[str] = mapped_column(String(100), nullable=False)
    corrected_category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    corrected_tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    corrected_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Metadata
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    is_correction: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # True = user changed AI prediction
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    problem: Mapped["Problem"] = relationship()
    user: Mapped["User"] = relationship()


class ClassificationMetrics(Base):
    """Aggregated metrics for classification performance tracking."""

    __tablename__ = "classification_metrics"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=generate_feedback_id
    )
    category_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Counts
    total_predictions: Mapped[int] = mapped_column(default=0, nullable=False)
    correct_predictions: Mapped[int] = mapped_column(default=0, nullable=False)
    user_corrections: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Per-priority accuracy
    priority_accuracy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    @property
    def accuracy(self) -> float:
        if self.total_predictions == 0:
            return 0.0
        return self.correct_predictions / self.total_predictions