import secrets
import string
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Boolean, DateTime, String, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RoleEnum


ROLE_PREFIXES = {
    RoleEnum.CITIZEN: "ctz",
    RoleEnum.STUDENT: "stu",
    RoleEnum.FACULTY: "fac",
    RoleEnum.UNIVERSITY_ADMIN: "uad",
    RoleEnum.INDUSTRY: "ind",
    RoleEnum.GOVERNMENT: "gov",
    RoleEnum.ADMIN: "adm",
}


def generate_user_id(role: RoleEnum) -> str:
    """Generate a human-readable user ID with role prefix.
    Format: {prefix}_{random_alphanumeric_8}
    Example: ctz_a3f2b1c9, stu_x7k9m2n4
    """
    prefix = ROLE_PREFIXES.get(role, "usr")
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(8))
    return f"{prefix}_{random_part}"


class User(Base):
    """USERS table — Phase 1 + Phase 2."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=lambda: generate_user_id(RoleEnum.CITIZEN)
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="role_enum", native_enum=True), nullable=False
    )
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    domain_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # For solvers
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships (Phase 2) - specify foreign_keys to resolve ambiguity
    problems_submitted: Mapped[List["Problem"]] = relationship(
        "Problem", 
        foreign_keys="Problem.submitter_id",
        back_populates="submitter"
    )
    solutions: Mapped[List["Solution"]] = relationship(
        "Solution",
        foreign_keys="Solution.author_id",
        back_populates="author"
    )

    def __init__(self, **kwargs):
        role = kwargs.get('role', RoleEnum.CITIZEN)
        if 'id' not in kwargs:
            kwargs['id'] = generate_user_id(role)
        super().__init__(**kwargs)