"""OTP table — stores short-lived one-time codes for email/phone verification."""
import secrets
import string
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def generate_otp_id() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "otp_" + "".join(secrets.choice(alphabet) for _ in range(10))


class OTP(Base):
    """OTP verification codes (plan.txt §— verify email/phone before activating account)."""

    __tablename__ = "otp"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=generate_otp_id)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # email or phone
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)  # register | verify | login
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
