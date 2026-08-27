from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RoutingTypeEnum, NotificationTypeEnum


class RoutingLog(Base):
    """ROUTING_LOG — plan.txt §7. Records which solvers a problem was routed to."""

    __tablename__ = "routing_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(String(20), ForeignKey("problems.id"), nullable=False, index=True)
    routed_to_type: Mapped[RoutingTypeEnum] = mapped_column(
        SAEnum(RoutingTypeEnum, name="routing_type_enum", native_enum=True), nullable=False
    )
    routed_to_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    problem = relationship("Problem", back_populates="routing_logs")
    routed_to = relationship("User")


class Notification(Base):
    """NOTIFICATIONS — plan.txt §7. In-app notifications."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[NotificationTypeEnum] = mapped_column(
        SAEnum(NotificationTypeEnum, name="notification_type_enum", native_enum=True),
        default=NotificationTypeEnum.GENERIC,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # problem/solution id
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User")
