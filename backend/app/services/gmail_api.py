"""Gmail API email delivery (OAuth2) — replaces SMTP app-password sending.

Setup (one time, ~5 min):
  1. Google Cloud Console → enable the **Gmail API** for your project.
  2. OAuth consent screen → add scope `https://www.googleapis.com/auth/gmail.send`,
     add your sender Gmail as a test user. For production, publish the app
     (OAuth apps in "Testing" mode get refresh tokens that expire in 7 days).
  3. Put the OAuth client ID/secret in .env as GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET.
  4. Run (logged in as the SENDER account — mail is sent as this account):
         python -m app.services.gmail_api url
     open the printed URL, approve, copy the code, then run:
         python -m app.services.gmail_api exchange <code>
     It prints GMAIL_REFRESH_TOKEN — paste it (plus GMAIL_SENDER, the same
     account) into .env / Render dashboard. Done; tokens refresh automatically.

Only stdlib + httpx (already a dependency). No google-api-python-client needed.
"""
import base64
import logging
import sys
import time
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger("gmail_api")

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
_OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
# Localhost redirect works without registering anything in Google Cloud Console.
_REDIRECT_URI = "http://localhost:8080"

# In-memory access-token cache: {"token": str, "expires_at": epoch}
_token_cache: dict = {}


def gmail_configured() -> bool:
    return bool(
        settings.GMAIL_CLIENT_ID
        and settings.GMAIL_CLIENT_SECRET
        and settings.GMAIL_REFRESH_TOKEN
        and settings.GMAIL_SENDER
    )


def build_consent_url() -> str:
    """OAuth consent URL — open in a browser logged in as the sender account."""
    params = urlencode(
        {
            "client_id": settings.GMAIL_CLIENT_ID,
            "redirect_uri": _REDIRECT_URI,
            "response_type": "code",
            "scope": GMAIL_SEND_SCOPE,
            "access_type": "offline",  # ask for a refresh token
            "prompt": "consent",  # force re-consent so a refresh token is issued
        }
    )
    return f"{_OAUTH_AUTH_URL}?{params}"


def exchange_code(code: str) -> dict:
    """Exchange the one-time consent code for access + refresh tokens."""
    resp = httpx.post(
        _OAUTH_TOKEN_URL,
        data={
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "code": code.strip(),
            "grant_type": "authorization_code",
            "redirect_uri": _REDIRECT_URI,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def _get_access_token() -> str:
    """Return a valid access token, refreshing via the stored refresh token."""
    now = time.time()
    cached = _token_cache.get("token")
    if cached and _token_cache.get("expires_at", 0) - 60 > now:
        return cached
    resp = httpx.post(
        _OAUTH_TOKEN_URL,
        data={
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "refresh_token": settings.GMAIL_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + int(data.get("expires_in", 3600))
    return _token_cache["token"]


def send_gmail(to_email: str, subject: str, body_text: str) -> bool:
    """Send a plain-text email through the Gmail API as GMAIL_SENDER."""
    if not gmail_configured():
        raise RuntimeError("Gmail API not configured (GMAIL_* settings missing).")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.GMAIL_SENDER}>"
    msg["To"] = to_email
    msg.set_content(body_text)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    token = _get_access_token()
    resp = httpx.post(
        _GMAIL_SEND_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"raw": raw},
        timeout=20,
    )
    if resp.status_code == 401:  # access token rejected — refresh once and retry
        _token_cache.clear()
        token = _get_access_token()
        resp = httpx.post(
            _GMAIL_SEND_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"raw": raw},
            timeout=20,
        )
    resp.raise_for_status()
    logger.info("Gmail API email sent to %s (id=%s)", to_email, resp.json().get("id"))
    return True


def main(argv: list[str]) -> int:
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        print("Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in backend/.env first.")
        return 1
    if argv == ["url"]:
        print("\n1. Make sure you are logged in as the SENDER Gmail account, then open:\n")
        print(build_consent_url())
        print(
            "\n2. Approve, copy the code from the redirect, then run:\n"
            "     python -m app.services.gmail_api exchange <code>"
        )
        return 0
    if len(argv) == 2 and argv[0] == "exchange":
        try:
            tokens = exchange_code(argv[1])
        except httpx.HTTPStatusError as exc:
            print(f"Exchange failed ({exc.response.status_code}): {exc.response.text}")
            return 1
        print("\nSUCCESS. Add this to backend/.env (and Render env vars):\n")
        refresh = tokens.get("refresh_token")
        if not refresh:
            print("No refresh token was issued. Remove prior consent for this app at")
            print("https://myaccount.google.com/permissions and run the 'url' step again.")
            return 1
        print(f"GMAIL_REFRESH_TOKEN={refresh}")
        print("\nAlso set GMAIL_SENDER to the Gmail account you just approved with.")
        return 0
    print("Usage:\n  python -m app.services.gmail_api url\n  python -m app.services.gmail_api exchange <code>")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
