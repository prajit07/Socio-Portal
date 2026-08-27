from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tag(Base):
    """TAGS taxonomy — plan.txt §7. Domain/category tags (Agri, Health, Water, ...)."""

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # slug e.g. "water_sanitation"
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    parent_id: Mapped[Optional[str]] = mapped_column(String(40), ForeignKey("tags.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ProblemTag(Base):
    """PROBLEM_TAGS link — plan.txt §7. AI tags with confidence scores."""

    __tablename__ = "problem_tags"
    __table_args__ = (UniqueConstraint("problem_id", "tag_id", name="uq_problem_tag"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(String(20), ForeignKey("problems.id"), nullable=False, index=True)
    tag_id: Mapped[str] = mapped_column(String(40), ForeignKey("tags.id"), nullable=False, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0..1 from AI

    tag = relationship("Tag")
    problem = relationship("Problem", back_populates="problem_tags")
