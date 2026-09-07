"""Local sklearn classifier — fast primary path for problem categorization.

Loads backend/app/ml/category_classifier.joblib (trained by Model_Training/train_classifier.py
on the 12-category taxonomy.json). Runs offline in ~5ms, no Cloudflare quota needed.

Order in ai_categorization.categorize(): local model -> Cloudflare LLM -> heuristic.
If model file or sklearn is missing, returns None so callers fall back cleanly.
"""
import os
from typing import Optional

from app.core.config import settings

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "category_classifier.joblib")
_bundle = None
_load_error: Optional[str] = None


def _load():
    global _bundle, _load_error
    if _bundle is not None or _load_error is not None:
        return _bundle
    if not os.path.exists(_MODEL_PATH):
        _load_error = "model file missing"
        return None
    try:
        import joblib
        _bundle = joblib.load(_MODEL_PATH)
        return _bundle
    except Exception as e:  # sklearn version mismatch etc. -> fall back
        _load_error = str(e)
        return None


def predict(title: str, description: str, transcript: Optional[str] = None):
    """Return (category_id, category_name, confidence) or None if unavailable."""
    bundle = _load()
    if not bundle:
        return None
    try:
        text = f"{title or ''} {description or ''} {transcript or ''}".strip()
        if not text:
            return None
        pipe = bundle["pipeline"]
        proba = None
        if hasattr(pipe, "predict_proba"):
            proba = pipe.predict_proba([text])[0]
            idx = int(proba.argmax())
            label = pipe.classes_[idx]
            conf = float(proba[idx])
        else:
            label = pipe.predict([text])[0]
            conf = 0.75
        name = next((c["name"] for c in bundle.get("categories", []) if c["id"] == label), label)
        # Low-confidence predictions defer to LLM/heuristic (threshold is tunable
        # via LOCAL_MIN_CONFIDENCE without redeploying the model).
        if conf < settings.LOCAL_MIN_CONFIDENCE:
            return None
        return label, name, round(conf, 3)
    except Exception:
        return None


def status() -> dict:
    bundle = _load()
    return {"loaded": bundle is not None,
            "path": _MODEL_PATH,
            "error": _load_error,
            "categories": len(bundle.get("categories", [])) if bundle else 0}
