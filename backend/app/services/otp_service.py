"""OTP generation, storage and delivery (plan.txt — email/phone verification).

- Codes are stored hashed (HMAC-SHA256 with JWT_SECRET as the key), never in plaintext.
- Email delivery uses Google SMTP when EMAIL_USER/EMAIL_PASS are set; otherwise the
  code is printed to the server console (dev mode) so the flow works without creds.
- `request_otp` returns the plaintext code ONLY in dev mode (email not configured),
  for easy local testing; in production it always returns None.
"""
import hashlib
import hmac
import logging
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.otp import OTP

logger = logging.getLogger("otp")


def generate_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(settings.OTP_LENGTH))


def _hash(code: str) -> str:
    return hmac.new(settings.JWT_SECRET.encode(), code.encode(), hashlib.sha256).hexdigest()


def _send_email(email: str, code: str, purpose: str) -> bool:
    """Send the OTP via SMTP. Returns True on success, False on any failure
    (so the caller can fall back to surfacing the code for local testing)."""
    if not settings.email_configured:
        logger.info("[DEV OTP] %s (%s): %s", email, purpose, code)
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Socio Connect verification code"
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_USER}>"
        msg["To"] = email
        msg.set_content(
            f"Your verification code is: {code}\n"
            f"It expires in {settings.OTP_TTL_SECONDS // 60} minute(s). "
            f"If you did not request this, you can ignore this email."
        )
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=20) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            server.send_message(msg)
        logger.info("OTP email sent to %s (%s)", email, purpose)
        return True
    except Exception as e:  # noqa: BLE001 - SMTP misconfig should not break the flow
        logger.error(
            "[OTP EMAIL FAILED] %s (%s): %s: %s — dev fallback code: %s",
            email,
            purpose,
            type(e).__name__,
            e,
            code,
        )
        return False


def request_otp(db: Session, identifier: str, purpose: str, channel: str = "email") -> Optional[str]:
    """Create a fresh OTP, invalidating any previous one for (identifier, purpose)."""
    db.query(OTP).filter(OTP.identifier == identifier, OTP.purpose == purpose).delete()
    code = generate_code()
    otp = OTP(
        identifier=identifier,
        purpose=purpose,
        code_hash=_hash(code),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_TTL_SECONDS),
        attempts=0,
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)
    sent = False
    if channel == "email":
        sent = _send_email(identifier, code, purpose)
    logger.info("OTP requested identifier=%s purpose=%s channel=%s sent=%s", identifier, purpose, channel, sent)
    # Only surface the plaintext code in the API when SMTP is NOT configured at all
    # (pure local dev with no sender creds). When configured, the code is delivered by
    # email and must never be exposed in the response — this forces the real SMTP path.
    return code if not settings.email_configured else None


def verify_otp(db: Session, identifier: str, code: str, purpose: str, max_attempts: int = 5) -> bool:
    otp = (
        db.query(OTP)
        .filter(OTP.identifier == identifier, OTP.purpose == purpose)
        .order_by(OTP.created_at.desc())
        .first()
    )
    if not otp:
        logger.warning("OTP verify FAILED (no active code) identifier=%s purpose=%s", identifier, purpose)
        return False
    # Normalize to UTC so the comparison is correct regardless of the DB session timezone.
    expires_at = otp.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(otp)
        db.commit()
        logger.warning("OTP verify FAILED (expired) identifier=%s purpose=%s", identifier, purpose)
        return False
    if otp.attempts >= max_attempts:
        logger.warning("OTP verify FAILED (attempts exhausted) identifier=%s purpose=%s", identifier, purpose)
        return False
    otp.attempts += 1
    if hmac.compare_digest(otp.code_hash, _hash(code)):
        db.delete(otp)
        db.commit()
        logger.info("OTP verify OK identifier=%s purpose=%s", identifier, purpose)
        return True
    db.commit()
    logger.warning(
        "OTP verify FAILED (invalid code) identifier=%s purpose=%s attempt=%d",
        identifier,
        purpose,
        otp.attempts,
    )
    return False
