import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, func, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _rand(prefix: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return f"{prefix}_" + "".join(secrets.choice(alphabet) for _ in range(10))


class Collaboration(Base):
    """COLLABORATIONS table — Phase 5 (industry picks up a proposal)."""

    __tablename__ = "collaborations"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("col"))
    proposal_id: Mapped[str] = mapped_column(String(20), ForeignKey("solutions.id"), nullable=False)
    industry_id: Mapped[str] = mapped_column(String(20), ForeignKey("industries.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), default="interested", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    industry: Mapped["Industry"] = relationship(back_populates="collaborations")
    milestones: Mapped[list["Milestone"]] = relationship(back_populates="collaboration", cascade="all, delete-orphan")
    ip_records: Mapped[list["IPRecord"]] = relationship(back_populates="collaboration", cascade="all, delete-orphan")
    impact_reports: Mapped[list["SocialImpactReport"]] = relationship(back_populates="collaboration", cascade="all, delete-orphan")


class Milestone(Base):
    """MILESTONES table — Phase 5 (collaboration progress tracking)."""

    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("mil"))
    collaboration_id: Mapped[str] = mapped_column(String(20), ForeignKey("collaborations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    collaboration: Mapped["Collaboration"] = relationship(back_populates="milestones")
    deliverables: Mapped[list["Deliverable"]] = relationship(back_populates="milestone", cascade="all, delete-orphan")


class Deliverable(Base):
    """DELIVERABLES table — files attached to a milestone."""

    __tablename__ = "deliverables"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("del"))
    milestone_id: Mapped[str] = mapped_column(String(20), ForeignKey("milestones.id"), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    milestone: Mapped["Milestone"] = relationship(back_populates="deliverables")


class IPRecord(Base):
    """IP_RECORDS table — patents/copyrights filed during a collaboration."""

    __tablename__ = "ip_records"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("ip"))
    collaboration_id: Mapped[str] = mapped_column(String(20), ForeignKey("collaborations.id"), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # patent|copyright|trademark|trade_secret
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # filed|granted|pending
    reference_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    collaboration: Mapped["Collaboration"] = relationship(back_populates="ip_records")


class SocialImpactReport(Base):
    """SOCIAL_IMPACT_REPORTS table — Phase 6 (gov visibility)."""

    __tablename__ = "social_impact_reports"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("imp"))
    collaboration_id: Mapped[str] = mapped_column(String(20), ForeignKey("collaborations.id"), nullable=False)
    beneficiaries_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    impact_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    collaboration: Mapped["Collaboration"] = relationship(back_populates="impact_reports")
