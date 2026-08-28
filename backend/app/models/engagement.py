import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


def _rand(prefix: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return f"{prefix}_" + "".join(secrets.choice(alphabet) for _ in range(10))


class Comment(Base):
    """COMMENTS table — engagement on problems/proposals/collaborations."""

    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("cmt"))
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # problem|solution|collaboration
    entity_id: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    author: Mapped[User] = relationship("User")


class Upvote(Base):
    """UPVOTES table — citizens upvote problems."""

    __tablename__ = "upvotes"
    __table_args__ = (UniqueConstraint("problem_id", "user_id", name="uq_upvote_problem_user"),)

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("up"))
    problem_id: Mapped[str] = mapped_column(String(20), ForeignKey("problems.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship("User")


class CitizenProfile(Base):
    """CITIZEN_PROFILES table — extra citizen details."""

    __tablename__ = "citizen_profiles"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("cpf"))
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), unique=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class AuditLog(Base):
    """AUDIT_LOG table — Phase 7 (admin oversight)."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("aud"))
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
