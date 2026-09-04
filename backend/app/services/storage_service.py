"""Evidence file storage (plan.txt §8 storage_service).

Two backends, selected with STORAGE_BACKEND:
  - "local" (default): writes to backend/uploads/, served by the API at /uploads/...
  - "s3": uploads to any S3-compatible bucket (AWS S3, Cloudflare R2,
    Backblaze B2, Supabase Storage, self-hosted MinIO) via boto3 and returns
    a public URL.

`save_file(content, filename)` keeps the same signature on both backends, so
callers (evidence API) work unchanged. Only `file_url` values differ.
"""
import io
import logging
import mimetypes
import os
import secrets
import string

from app.core.config import settings

logger = logging.getLogger("storage")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")

_ALLOWED_EXT = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".mp3", ".wav", ".ogg",
    ".mp4", ".webm", ".mov", ".txt", ".doc", ".docx",
}


def _random_stored_name(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_EXT:
        ext = ""
    rand = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{rand}{ext}"


def _save_local(content: bytes, filename: str) -> str:
    """Persist bytes to backend/uploads/; return a public-relative URL path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored = _random_stored_name(filename)
    with open(os.path.join(UPLOAD_DIR, stored), "wb") as f:
        f.write(content)
    return f"/uploads/{stored}"


def _s3_client():
    """Build a boto3 S3 client for AWS or any S3-compatible endpoint."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise RuntimeError(
            "STORAGE_BACKEND=s3 requires boto3 (`pip install boto3`)."
        ) from exc
    if not settings.s3_configured:
        raise RuntimeError(
            "STORAGE_BACKEND=s3 requires S3_BUCKET, S3_ACCESS_KEY and "
            "S3_SECRET_KEY to be set."
        )
    session = boto3.session.Session(
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION or None,
    )
    # Empty endpoint = real AWS S3 (default virtual-hosted addressing).
    # A custom endpoint (R2/B2/Supabase/MinIO) needs path-style addressing.
    endpoint = settings.S3_ENDPOINT_URL.strip() or None
    client_kwargs: dict = {
        "endpoint_url": endpoint,
        "region_name": settings.S3_REGION or None,
    }
    if endpoint:
        client_kwargs["config"] = Config(s3={"addressing_style": "path"})
    return session.client("s3", **client_kwargs)


def _save_s3(content: bytes, filename: str) -> str:
    """Upload bytes to the S3 bucket; return a public URL for file_url."""
    stored = _random_stored_name(filename)
    key = f"evidence/{stored}"
    content_type = mimetypes.guess_type(stored)[0] or "application/octet-stream"

    client = _s3_client()
    client.upload_fileobj(
        io.BytesIO(content),
        settings.S3_BUCKET,
        key,
        ExtraArgs={"ContentType": content_type},
    )

    public_base = settings.S3_PUBLIC_BASE_URL.strip()
    if public_base:
        # R2 public bucket (https://pub-<id>.r2.dev), CDN, or Supabase public URL.
        return f"{public_base.rstrip('/')}/{key}"
    endpoint = settings.S3_ENDPOINT_URL.strip()
    if endpoint:
        # Custom endpoint without a public base (e.g. local MinIO).
        return f"{endpoint.rstrip('/')}/{settings.S3_BUCKET}/{key}"
    # Real AWS S3 with public-read bucket policy.
    return f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"


def save_file(content: bytes, filename: str) -> str:
    """Persist evidence bytes; return the URL stored in evidence.file_url."""
    if settings.storage_is_s3:
        url = _save_s3(content, filename or "upload.bin")
        logger.info("Stored evidence in S3 bucket %s: %s", settings.S3_BUCKET, url)
        return url
    return _save_local(content, filename or "upload.bin")
