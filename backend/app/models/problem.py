import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, String, func, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RoleEnum, ProblemStatusEnum, ProblemPriorityEnum, SolutionStatusEnum


def generate_problem_id() -> str:
    """Generate a human-readable problem ID."""
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(10))
    return f"prob_{random_part}"


def generate_solution_id() -> str:
    """Generate a human-readable solution ID."""
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(10))
    return f"sol_{random_part}"


class Problem(Base):
    """PROBLEMS table — Phase 2."""

    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=generate_problem_id
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # Evidence files/recordings
    evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Transcribed voice/text evidence
    
    # Location for map feature
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Tags and categorization
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # User-provided tags
    ai_tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # AI-generated tags
    ai_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # AI categorization
    ai_priority: Mapped[Optional[ProblemPriorityEnum]] = mapped_column(
        SAEnum(ProblemPriorityEnum, name="priority_enum", native_enum=True), nullable=True
    )
    ai_duplicate_check: Mapped[Optional[bool]] = mapped_column(nullable=True, default=False)
    ai_duplicate_of: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # ID of duplicate problem
    
    # Status and workflow
    status: Mapped[ProblemStatusEnum] = mapped_column(
        SAEnum(ProblemStatusEnum, name="problem_status_enum", native_enum=True),
        default=ProblemStatusEnum.PENDING_VALIDATION,
        nullable=False
    )
    
    # Assigned solver (HEI team, industry, etc.)
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    assigned_to: Mapped[Optional["User"]] = relationship(foreign_keys=[assigned_to_id])
    
    # Submitter
    submitter_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    submitter: Mapped["User"] = relationship(foreign_keys=[submitter_id], back_populates="problems_submitted")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    solutions: Mapped[list["Solution"]] = relationship(back_populates="problem", cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="problem", cascade="all, delete-orphan")
    problem_tags: Mapped[list["ProblemTag"]] = relationship(back_populates="problem", cascade="all, delete-orphan")
    routing_logs: Mapped[list["RoutingLog"]] = relationship(back_populates="problem", cascade="all, delete-orphan")


class Solution(Base):
    """SOLUTIONS table — Phase 2."""

    __tablename__ = "solutions"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=generate_solution_id
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Solution details
    approach: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    estimated_timeline: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estimated_budget: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status
    status: Mapped[SolutionStatusEnum] = mapped_column(
        SAEnum(SolutionStatusEnum, name="solution_status_enum", native_enum=True),
        default=SolutionStatusEnum.DRAFT,
        nullable=False
    )
    
    # Links
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_urls: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    
    # Problem reference
    problem_id: Mapped[str] = mapped_column(String(20), ForeignKey("problems.id"), nullable=False)
    problem: Mapped["Problem"] = relationship(back_populates="solutions")
    
    # Author (solver)
    author_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship(back_populates="solutions")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )