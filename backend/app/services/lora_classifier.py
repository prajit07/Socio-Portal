"""Phase 2 (+4): LoRA provider abstraction for problem classification.

Providers (selected by settings.LORA_PROVIDER):
  cloudflare — Workers AI @cf/...-lora with raw:true, lora:<finetune>
  modal      — POST {MODAL_ENDPOINT} {"text": ...} -> {"label": <10-label>}
  off        — disabled (default until a finetune is uploaded)

LoRA emits the 10 SIH training labels; LABEL_MAP_10_TO_12 converts to the 12
backend taxonomy ids. Two mappings are LOSSY by design and flagged in notes:
  Accessibility -> public_safety (no dedicated backend class)
  Environment + Energy -> energy_environment (shared backend class)
Fix properly by adding taxonomy entries, not by tweaking this map.

Returns the same dict shape as ai_categorization.categorize() so the caller
can swap or shadow-compare providers.
"""
import json
import urllib.request
from typing import Optional

from app.core.config import settings
from app.models.enums import ProblemPriorityEnum

LABELS_10 = [
    "Education", "Agriculture", "Healthcare", "Water Resources", "Environment",
    "Energy", "Urban Development", "Accessibility", "Public Administration",
    "Rural Livelihoods",
]

# (backend_id, backend_name, lossy?)
LABEL_MAP_10_TO_12 = {    "Education": ("education", "Education", False),
    "Agriculture": ("agriculture", "Agriculture & Rural", False),
    "Healthcare": ("health", "Health & Healthcare", False),
    "Water Resources": ("water_sanitation", "Water & Sanitation", False),
    "Environment": ("energy_environment", "Energy & Environment", True),
    "Energy": ("energy_environment", "Energy & Environment", True),
    "Urban Development": ("housing_urban", "Housing & Urban Development", False),
    "Accessibility": ("public_safety", "Public Safety & Security", True),
    "Public Administration": ("digital_governance", "Digital Governance", False),
    "Rural Livelihoods": ("livelihood", "Livelihood & Employment", False),
}


def build_prompt(text: str) -> str:
    """Canonical LoRA prompt — byte-identical to the training template.

    The adapter was trained on rows shaped exactly like this (see
    Model_Training/build_lora_dataset.py), and Cloudflare inference runs with
    raw:true, so the model continues verbatim from this prompt. Every caller
    (Cloudflare provider here, probe_lora.py, modal_app.py) MUST use this
    helper — a mismatched template silently degrades label accuracy.
    """
    return f"### Human: Categorize this societal challenge: {(text or '').strip()} ### Assistant:"


def _parse_label(text: str) -> Optional[str]:
    for lab in LABELS_10:
        if lab.lower() in (text or "").lower():
            return lab
    return None


def _query_cloudflare(problem_text: str) -> Optional[str]:
    if not settings.lora_enabled or settings.LORA_PROVIDER.strip().lower() != "cloudflare":
        return None
    url = (f"https://api.cloudflare.com/client/v4/accounts/"
           f"{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{settings.CLOUDFLARE_LORA_MODEL}")
    body = {"messages": [{"role": "user", "content": build_prompt(problem_text)}],
            # NOTE: docs show "raw": "true" (string); boolean True is sent here —
            # confirm acceptance during Phase-1 probe, normalize if rejected.
            "raw": True, "lora": settings.CLOUDFLARE_LORA_FINETUNE,
            "max_tokens": 20, "temperature": 0.0}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {settings.CLOUDFLARE_AI_API_KEY}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=settings.CLASSIFY_TIMEOUT) as r:
            res = json.loads(r.read().decode()).get("result", {})
        text = res.get("response", "") if isinstance(res, dict) else str(res)
        return _parse_label(text)
    except Exception:
        return None


def _query_modal(problem_text: str) -> Optional[str]:
    """Phase 4: Modal fallback. Endpoint serves the same 10-label adapter."""
    if settings.LORA_PROVIDER.strip().lower() != "modal" or not settings.MODAL_ENDPOINT:
        return None
    req = urllib.request.Request(settings.MODAL_ENDPOINT,
                                 data=json.dumps({"text": problem_text}).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": f"Bearer {settings.MODAL_API_KEY}"}
                                             if settings.MODAL_API_KEY else {})})
    try:
        with urllib.request.urlopen(req, timeout=settings.CLASSIFY_TIMEOUT) as r:
            return _parse_label(json.loads(r.read().decode()).get("label", ""))
    except Exception:
        return None


def classify(title: str, description: str, transcript: Optional[str] = None):
    """Return categorize()-shaped dict via LoRA, or None if disabled/failed."""
    if not settings.lora_enabled:
        return None
    problem_text = f"{title or ''} {description or ''} {transcript or ''}".strip()
    if not problem_text:
        return None
    label10 = _query_modal(problem_text)
    provider = "modal"
    if label10 is None and settings.LORA_PROVIDER.strip().lower() == "cloudflare":
        label10 = _query_cloudflare(problem_text)
        provider = "cloudflare"
    if label10 is None:
        return None
    cid, cname, lossy = LABEL_MAP_10_TO_12[label10]
    from app.services.ai_categorization import _score_priority
    return {"category_id": cid, "category_name": cname,
            "tags": [{"id": cid, "name": cname, "confidence": 0.9}],
            "priority": _score_priority(title, description, transcript, 2),
            "_lora": {"provider": provider, "label10": label10, "lossy_map": lossy}}


def shadow_compare(baseline: dict, lora_result: Optional[dict]) -> dict:
    """Compare baseline vs LoRA for shadow-mode logging. No DB writes here."""
    if not lora_result:
        return {"lora_available": False, "agree": None}
    return {"lora_available": True,
            "agree": baseline.get("category_id") == lora_result.get("category_id"),
            "baseline": baseline.get("category_id"),
            "lora": lora_result.get("category_id"),
            "label10": lora_result.get("_lora", {}).get("label10"),
            "lossy_map": lora_result.get("_lora", {}).get("lossy_map", False)}
