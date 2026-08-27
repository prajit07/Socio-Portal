"""AI categorization, tagging and priority scoring.

Primary path: Cloudflare Workers AI (settings.CLOUDFLARE_*). If the key is missing
or the call fails, a deterministic heuristic (taxonomy keyword matching) is used so
the pipeline always works.
"""
import json
import os
import re
from typing import Optional

from app.core.config import settings
from app.models.enums import ProblemPriorityEnum
from app.services.cloudflare_ai import chat

_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "taxonomy.json")


def _load_taxonomy():
    with open(_TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["categories"]


CATEGORIES = _load_taxonomy()
_ID_TO_NAME = {c["id"]: c["name"] for c in CATEGORIES}
_TAXONOMY_LIST = "\n".join(f"- {c['id']}: {c['name']}" for c in CATEGORIES)


def _tokenize(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _extract_json(text: str):
    """Pull the first JSON object out of an LLM response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _heuristic(title, description, transcript, tags):
    text = f"{title} {description} {transcript or ''} {' '.join(tags or [])}"
    tokens = _tokenize(text)
    scores = []
    for cat in CATEGORIES:
        hits = sum(1 for kw in cat["keywords"] if kw in tokens)
        if hits:
            scores.append((hits, cat))
    scores.sort(key=lambda x: x[0], reverse=True)
    if scores:
        top_hits, top_cat = scores[0]
        category_id = top_cat["id"]
        category_name = top_cat["name"]
        tag_candidates = scores[:3]
    else:
        category_id, category_name, tag_candidates = "general", "General", []

    out_tags = []
    for hits, cat in tag_candidates:
        out_tags.append({"id": cat["id"], "name": cat["name"], "confidence": round(min(1.0, 0.5 + 0.1 * hits), 2)})
    for t in tags or []:
        if t and t.lower() not in [x["id"] for x in out_tags]:
            out_tags.append({"id": t.lower().replace(" ", "_"), "name": t, "confidence": 0.6})

    priority = _score_priority(title, description, transcript, top_hits if scores else 0)
    return {
        "category_id": category_id,
        "category_name": category_name,
        "tags": out_tags,
        "priority": priority,
    }


def _llm_categorize(title, description, transcript, tags):
    system = (
        "You are a classification engine for a civic-tech portal (InnoSphere). "
        "Classify the reported problem into ONE category and assign 1-4 relevant tags. "
        "Choose the category id from this taxonomy (use the exact id slug):\n"
        f"{_TAXONOMY_LIST}\n"
        "Respond with STRICT JSON only, no prose, in this shape:\n"
        '{"category_id": "<id>", "category_name": "<human name>", '
        '"tags": [{"id": "<id>", "name": "<human name>", "confidence": 0.0-1.0}], '
        '"priority": "low|medium|high|critical"}'
    )
    user = (
        f"Title: {title}\nDescription: {description}\n"
        f"Transcript: {transcript or 'none'}\nUser tags: {', '.join(tags or []) or 'none'}"
    )
    raw = chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
    if not raw:
        return None
    parsed = _extract_json(raw)
    if not parsed or "category_name" not in parsed:
        return None
    # Normalise / validate against taxonomy when possible
    cid = parsed.get("category_id")
    if cid not in _ID_TO_NAME:
        # try to match by name
        name = parsed.get("category_name", "").lower()
        matched = next((c for c in CATEGORIES if c["name"].lower() == name), None)
        if matched:
            cid, parsed["category_name"] = matched["id"], matched["name"]
        else:
            cid = cid or "general"
            parsed["category_name"] = parsed.get("category_name") or "General"
    tags_out = []
    for t in parsed.get("tags", []):
        tid = str(t.get("id") or "").lower().replace(" ", "_")
        if not tid:
            continue
        tags_out.append({
            "id": tid,
            "name": t.get("name") or _ID_TO_NAME.get(tid, tid),
            "confidence": float(t.get("confidence", 0.7)),
        })
    try:
        priority = ProblemPriorityEnum(parsed.get("priority", "medium"))
    except ValueError:
        priority = ProblemPriorityEnum.MEDIUM
    return {
        "category_id": cid,
        "category_name": parsed["category_name"],
        "tags": tags_out,
        "priority": priority,
    }


def categorize(title: str, description: str, transcript: Optional[str] = None, tags: Optional[list[str]] = None):
    """Return {category_id, category_name, tags:[{id,name,confidence}], priority}. Uses Cloudflare LLM, falls back to heuristic."""
    if settings.ai_enabled:
        llm = _llm_categorize(title, description, transcript, tags)
        if llm:
            return llm
    return _heuristic(title, description, transcript, tags)


def _score_priority(title, description, transcript, keyword_hits) -> ProblemPriorityEnum:
    text = f"{(title or '')} {(description or '')} {transcript or ''}".lower()
    critical_kw = ["life threatening", "death", "disaster", "catastrophe", "fire", "collapsed", "epidemic", "poison"]
    high_kw = ["urgent", "critical", "emergency", "dangerous", "hazard", "accident", "outbreak", "flood", "contamination"]
    if any(k in text for k in critical_kw):
        return ProblemPriorityEnum.CRITICAL
    if any(k in text for k in high_kw) or keyword_hits >= 3:
        return ProblemPriorityEnum.HIGH
    if keyword_hits >= 1:
        return ProblemPriorityEnum.MEDIUM
    return ProblemPriorityEnum.LOW
