import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Float, JSON, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RoleEnum


def _rand(prefix: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return f"{prefix}_" + "".join(secrets.choice(alphabet) for _ in range(10))


class University(Base):
    """UNIVERSITIES table — Phase 4 (org record for HEIs)."""

    __tablename__ = "universities"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("uni"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    registration_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    members: Mapped[list["UniversityMember"]] = relationship(back_populates="university", cascade="all, delete-orphan")


class UniversityMember(Base):
    """UNIVERSITY_MEMBERS table — links a User (student/faculty) to a University."""

    __tablename__ = "university_members"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("umem"))
    university_id: Mapped[str] = mapped_column(String(20), ForeignKey("universities.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    member_role: Mapped[str] = mapped_column(String(20), default="student", nullable=False)  # student|faculty_mentor|admin
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # student's department
    roll_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # student's roll number
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    university: Mapped["University"] = relationship(back_populates="members")


class Industry(Base):
    """INDUSTRIES table — Phase 5 (org record for companies/startups)."""

    __tablename__ = "industries"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("ind"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)  # startup|msme|corporate|csr|research_institution|innovation_hub
    registration_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    domain_tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    collaborations: Mapped[list["Collaboration"]] = relationship(back_populates="industry", cascade="all, delete-orphan")
