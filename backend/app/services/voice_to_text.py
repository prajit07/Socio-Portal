"""Voice-to-text service — plan.txt §8.1.

Primary path: Cloudflare Workers AI `@cf/openai/whisper`. Falls back to a mock
transcript when the key is missing or the call fails, so uploads still succeed.
"""
from typing import Optional

from app.core.config import settings
from app.services.cloudflare_ai import transcribe


def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    """Return transcript for the given audio bytes."""
    if settings.ai_enabled:
        text = transcribe(file_bytes)
        if text:
            return text.strip()
    return (
        "[Auto-transcribed (mock) — connect an STT provider to replace this text.] "
        f"Audio '{filename}' received ({len(file_bytes)} bytes)."
    )
