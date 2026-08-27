"""Local file storage for evidence uploads (plan.txt §8 storage_service).

Swap for S3/GCS by implementing `save_file` to upload and return a public URL.
"""
import os
import secrets
import string
from typing import Optional

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

_ALLOWED_EXT = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".mp3", ".wav", ".ogg",
    ".mp4", ".webm", ".mov", ".txt", ".doc", ".docx",
}


def save_file(content: bytes, filename: str) -> str:
    """Persist bytes to disk; return a public-relative URL path served by the API."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_EXT:
        ext = ""
    rand = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    stored = f"{rand}{ext}"
    with open(os.path.join(UPLOAD_DIR, stored), "wb") as f:
        f.write(content)
    return f"/uploads/{stored}"
