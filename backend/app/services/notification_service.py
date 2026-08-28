"""Notification service — plan.txt §6 (notification_service.py).

Central service for:
  - Creating DB notification records.
  - Optionally delivering alert emails in a background thread (non-blocking).

Usage:
    from app.services.notification_service import create_notification

    create_notification(
        db,
        user_id="ctz_abc123",
        message="Your problem has been validated.",
        notif_type=NotificationTypeEnum.STATUS_UPDATED,
        reference_id="prob_xyz",
        send_email=True,  # optional; requires EMAIL_USER/EMAIL_PASS in .env
        email_address="user@example.com",
    )
"""
import logging
import smtplib
import ssl
import threading
from email.message import EmailMessage
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.routing import Notification
from app.models.enums import NotificationTypeEnum

logger = logging.getLogger("notification_service")


def _send_email_async(to_email: str, subject: str, body: str) -> None:
    """Send email in a background thread so it never blocks the request cycle."""
    def _do_send():
        if not settings.email_configured:
            logger.info("[DEV NOTIFY] To: %s | %s | %s", to_email, subject, body)
            return
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_USER}>"
            msg["To"] = to_email
            msg.set_content(body)
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=20) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                server.send_message(msg)
            logger.info("Notification email sent to %s", to_email)
        except Exception as exc:
            logger.error("Notification email failed to %s: %s", to_email, exc)

    t = threading.Thread(target=_do_send, daemon=True)
    t.start()


def create_notification(
    db: Session,
    user_id: str,
    message: str,
    notif_type: NotificationTypeEnum = NotificationTypeEnum.GENERIC,
    reference_id: Optional[str] = None,
    send_email: bool = False,
    email_address: Optional[str] = None,
) -> Notification:
    """Create a DB notification record and optionally deliver an email alert.

    Args:
        db:            SQLAlchemy session (caller must call db.commit() after).
        user_id:       Recipient user ID.
        message:       Notification message text.
        notif_type:    Notification type enum value.
        reference_id:  Optional problem/solution/collaboration ID for deep-link.
        send_email:    If True, attempts to send an alert email.
        email_address: Recipient email for the alert (required if send_email=True).

    Returns:
        The Notification ORM object (not yet committed).
    """
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        message=message,
        reference_id=reference_id,
    )
    db.add(notif)

    if send_email and email_address:
        subject = "Socio Connect — New Notification"
        body = (
            f"{message}\n\n"
            "Log in to Socio Connect to view details:\n"
            "http://localhost:5174/notifications\n\n"
            "— The Socio Connect Team"
        )
        _send_email_async(email_address, subject, body)

    return notif


def broadcast_notification(
    db: Session,
    user_ids: list[str],
    message: str,
    notif_type: NotificationTypeEnum = NotificationTypeEnum.GENERIC,
) -> list[Notification]:
    """Create notifications for multiple users at once (e.g. admin broadcast)."""
    notifications = []
    for uid in user_ids:
        n = Notification(user_id=uid, type=notif_type, message=message)
        db.add(n)
        notifications.append(n)
    return notifications
