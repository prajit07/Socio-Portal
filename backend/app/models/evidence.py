from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EvidenceTypeEnum


def generate_evidence_id() -> str:
    import secrets
    import string

    alphabet = string.ascii_lowercase + string.digits
    return "ev_" + "".join(secrets.choice(alphabet) for _ in range(10))


class Evidence(Base):
    """EVIDENCE table — plan.txt §7. Stores problem evidence media + transcripts."""

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=generate_evidence_id)
    problem_id: Mapped[str] = mapped_column(String(20), ForeignKey("problems.id"), nullable=False, index=True)
    type: Mapped[EvidenceTypeEnum] = mapped_column(
        SAEnum(EvidenceTypeEnum, name="evidence_type_enum", native_enum=True), nullable=False
    )
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Filled by voice-to-text
    meta: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)  # free-form JSON-ish notes
    uploaded_by_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    problem = relationship("Problem", back_populates="evidence")
