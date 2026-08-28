import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _rand(prefix: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return f"{prefix}_" + "".join(secrets.choice(alphabet) for _ in range(10))


class Team(Base):
    """TEAMS table — Phase 4 (university project team for a problem)."""

    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("team"))
    problem_id: Mapped[str] = mapped_column(String(20), ForeignKey("problems.id"), nullable=False)
    university_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("universities.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_by: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    members: Mapped[list["TeamMember"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    proposals: Mapped[list["Solution"]] = relationship(back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """TEAM_MEMBERS table — students/faculty on a team."""

    __tablename__ = "team_members"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=lambda: _rand("tmem"))
    team_id: Mapped[str] = mapped_column(String(20), ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)  # e.g. lead, mentor, member
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="members")
