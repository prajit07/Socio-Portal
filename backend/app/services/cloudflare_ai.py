"""Cloudflare Workers AI client (plan.txt §8 — pluggable LLM provider).

Uses the Cloudflare REST endpoint:
  POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}
All calls are best-effort: on any failure they return None so callers fall back
to the deterministic heuristic engine. The API key is read from settings only.
"""
import base64
import json
import urllib.request
import urllib.error

from app.core.config import settings

_API_BASE = "https://api.cloudflare.com/client/v4/accounts"


def _post(model: str, payload: dict, timeout: int = 40):
    if not (settings.CLOUDFLARE_ACCOUNT_ID and settings.CLOUDFLARE_AI_API_KEY):
        return None
    url = f"{_API_BASE}/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_AI_API_KEY}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    if not data.get("success"):
        return None
    return data.get("result")


def chat(messages: list, model: str = None, max_tokens: int = 700, temperature: float = 0.2) -> str | None:
    """Return the assistant text for a chat completion, or None on failure."""
    model = model or settings.CLOUDFLARE_AI_MODEL
    result = _post(model, {"messages": messages, "max_tokens": max_tokens, "temperature": temperature})
    if not result:
        return None
    # Cloudflare returns different formats depending on model:
    # 1. {response: "..."} or {content: "..."} (older models)
    # 2. {choices: [{message: {content: "..."}}]} (OpenAI-compatible models like llama-3.1)
    if "choices" in result and result["choices"]:
        return result["choices"][0].get("message", {}).get("content")
    return result.get("response") or result.get("content")


def transcribe(audio_bytes: bytes) -> str | None:
    """Transcribe audio via @cf/openai/whisper. Returns text or None on failure."""
    if not audio_bytes:
        return None
    b64 = base64.b64encode(audio_bytes).decode()
    result = _post("@cf/openai/whisper", {"audio": b64})
    if not result:
        return None
    return result.get("text")
