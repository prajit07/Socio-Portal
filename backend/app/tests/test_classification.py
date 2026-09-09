"""Classification pipeline tests (production hardening).

Pure unit tests — no DB, no network, no Cloudflare creds needed:
- prompt template is byte-identical to the training format
- 10->12 label map covers all LoRA labels with valid taxonomy ids
- shadow comparison logic (agree / disagree / unavailable)
- LoRA disabled by default (safe production default)
- local sklearn artifact loads and predicts sanely (when sklearn installed)
- /classification/status endpoint shape + role gating
"""
import json
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.models.enums import RoleEnum
from app.services import lora_classifier as lora
from app.services import local_classifier as local
from app.api.v1.classification_feedback import get_status

TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "taxonomy.json")


@pytest.fixture()
def taxonomy_ids():
    with open(TAXONOMY_PATH, encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    return {c["id"] for c in cats}


def test_build_prompt_matches_training_template():
    assert lora.build_prompt("Potholes on MG Road") == (
        "### Human: Categorize this societal challenge: Potholes on MG Road ### Assistant:"
    )
    # whitespace is stripped so prompts are canonical
    assert lora.build_prompt("  hello  ") == (
        "### Human: Categorize this societal challenge: hello ### Assistant:"
    )


def test_label_map_covers_all_lora_labels(taxonomy_ids):
    assert set(lora.LABEL_MAP_10_TO_12) == set(lora.LABELS_10)
    assert len(lora.LABELS_10) == 10
    for lab10, (cid, _cname, lossy) in lora.LABEL_MAP_10_TO_12.items():
        assert cid in taxonomy_ids, f"{lab10} maps to unknown taxonomy id {cid}"
        assert isinstance(lossy, bool)


def test_parse_label_picks_canonical_label():
    assert lora._parse_label("Water Resources") == "Water Resources"
    assert lora._parse_label("  public administration.  ") == "Public Administration"
    assert lora._parse_label("something entirely different") is None


def test_shadow_compare_agree_disagree_missing():
    base = {"category_id": "health"}
    lo = {"category_id": "health", "_lora": {"label10": "Healthcare", "lossy_map": False}}
    assert lora.shadow_compare(base, lo) == {
        "lora_available": True, "agree": True, "baseline": "health",
        "lora": "health", "label10": "Healthcare", "lossy_map": False,
    }
    lo2 = {"category_id": "health", "_lora": {"label10": "Healthcare", "lossy_map": False}}
    assert lora.shadow_compare({"category_id": "education"}, lo2)["agree"] is False
    assert lora.shadow_compare(base, None) == {"lora_available": False, "agree": None}


def test_classify_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "LORA_PROVIDER", "off")
    assert lora.classify("Anything", "Any description") is None
    assert settings.lora_enabled is False


def test_local_predict_smoke(taxonomy_ids):
    """Artifact + sklearn present -> valid tuple; missing -> clean None."""
    res = local.predict("Sewage overflow on main road", "Dirty water near school")
    if res is None:
        # sklearn or model file missing in this env — loader must fail cleanly
        assert local.status()["loaded"] is False
        return
    cid, _name, conf = res
    assert cid in taxonomy_ids
    assert 0.0 <= conf <= 1.0
    assert local.status()["loaded"] is True
    assert local.predict("", "") is None


def test_status_endpoint_shape_and_gating(monkeypatch):
    monkeypatch.setattr(settings, "LORA_PROVIDER", "off")
    gov = SimpleNamespace(role=RoleEnum.GOVERNMENT)
    res = get_status(gov)
    assert res["order"] == ["local_sklearn", "lora", "cloudflare_llm", "heuristic"]
    assert isinstance(res["local_sklearn"]["loaded"], bool)
    assert res["lora"]["enabled"] is False
    assert res["lora"]["shadow_mode"] is True
    assert res["heuristic"] == {"enabled": True}
    assert isinstance(res["local_min_confidence"], float)

    citizen = SimpleNamespace(role=RoleEnum.CITIZEN)
    with pytest.raises(HTTPException):
        get_status(citizen)


def test_embedding_supported_false_when_column_missing(monkeypatch):
    """Column check must fail safe (False), never raise — e.g. Clever Cloud
    without pgvector, or SQLite in tests. Cached per database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.services import duplicate_detection as dd

    monkeypatch.setattr(dd, "_PGVECTOR_AVAILABLE", True)
    dd._support_cache.clear()
    eng = create_engine("sqlite://")
    with Session(eng) as db:
        assert dd.embedding_supported(db) is False
        assert dd.embedding_supported(db) is False  # served from cache
