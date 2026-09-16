"""Duplicate detection — plan.txt §8.4.

Primary path: pgvector cosine-similarity search using problem embeddings.
Falls back to Jaccard token overlap when pgvector is unavailable or embeddings
have not been generated.

Embedding generation:
  - Uses Cloudflare Workers AI `@cf/baai/bge-small-en-v1.5` (384-dim) when configured.
  - Falls back to a simple TF-IDF-inspired vector when LLM is unavailable.
"""
import json
import math
import os
import re
import struct
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.problem import Problem
from app.models.enums import ProblemStatusEnum

THRESHOLD = 0.6
EMBEDDING_DIM = 384

# Check pgvector availability at import time
try:
    from pgvector.sqlalchemy import Vector
    from sqlalchemy import text
    _PGVECTOR_AVAILABLE = True
except ImportError:
    _PGVECTOR_AVAILABLE = False


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------
def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _token_overlap(a: str, b: str) -> float:
    """Jaccard similarity (fallback when no embeddings)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---------------------------------------------------------------------------
# Embedding generation
# ---------------------------------------------------------------------------
def _cloudflare_embed(text: str) -> Optional[list[float]]:
    """Generate embedding via Cloudflare Workers AI."""
    if not settings.ai_enabled:
        return None
    try:
        from app.services.cloudflare_ai import _post
        result = _post(
            "@cf/baai/bge-small-en-v1.5",
            {"input": text},
            timeout=12,
        )
        if result and "data" in result and len(result["data"]) > 0:
            return result["data"][0].get("embedding")
        if result and "embedding" in result:
            return result["embedding"]
    except Exception:
        pass
    return None


def _heuristic_embed(text: str) -> list[float]:
    """Deterministic TF-IDF-inspired 384-dim vector as fallback.
    Uses token hashing into fixed buckets with log-frequency weighting."""
    tokens = _tokens(text)
    vec = [0.0] * EMBEDDING_DIM
    for tok in tokens:
        h = int.from_bytes(tok.encode()[:4].ljust(4, b"\x00"), "big")
        idx = h % EMBEDDING_DIM
        # Simple log-frequency weighting
        vec[idx] += 1.0 + math.log(1 + len(tok))
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def generate_embedding(text: str) -> list[float]:
    """Return a 384-dim embedding for the given text."""
    emb = _cloudflare_embed(text)
    if emb and len(emb) == EMBEDDING_DIM:
        return emb
    return _heuristic_embed(text)


# ---------------------------------------------------------------------------
# Cosine similarity via pgvector
# ---------------------------------------------------------------------------
def _pgvector_candidates(db: Session, embedding: list[float], threshold: float, exclude_id: str) -> list[dict]:
    """Use pgvector <=> (cosine distance) operator to find similar problems."""
    if not _PGVECTOR_AVAILABLE:
        return []
    try:
        # Parameterized query: avoids building a ~3KB SQL string per request,
        # lets Postgres reuse the plan + IVFFlat index, and closes SQL-injection.
        distance_cutoff = 1.0 - threshold
        rows = (
            db.query(
                Problem.id,
                Problem.title,
                Problem.address,
                text("embedding <=> :emb ::vector AS distance").bindparams(emb=json.dumps(embedding)),
            )
            .filter(Problem.id != exclude_id)
            .filter(Problem.embedding.isnot(None))
            .filter(Problem.status.in_([ProblemStatusEnum.OPEN, ProblemStatusEnum.VALIDATED]))
            .filter(text("embedding <=> :emb2 ::vector < :cutoff").bindparams(
                emb2=json.dumps(embedding), cutoff=distance_cutoff))
            .order_by(text("embedding <=> :emb3 ::vector").bindparams(emb3=json.dumps(embedding)))
            .limit(20)
            .all()
        )
        results = []
        for row in rows:
            distance = float(row[3]) if row[3] is not None else 1.0
            similarity = 1.0 - distance
            if similarity >= threshold:
                results.append({
                    "problem_id": row[0],
                    "title": row[1],
                    "address": row[2],
                    "similarity": round(similarity, 4),
                    "method": "pgvector_cosine",
                })
        return results
    except Exception:
        # pgvector column may not exist yet; fall back silently
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def find_duplicates(db: Session, problem: Problem, threshold: float = THRESHOLD) -> list[dict]:
    """Return list of {problem_id, title, similarity, method} for likely duplicates.

    Strategy:
      1. Try pgvector cosine similarity (fast, accurate) if available.
      2. Fall back to Jaccard token overlap.
    District proximity boosts the threshold by 0.15 (same-district problems are
    more likely to be true duplicates).
    """
    text_content = f"{problem.title} {problem.description} {problem.evidence_text or ''}"

    # --- Path 1: pgvector embedding search ---
    embedding = generate_embedding(text_content)
    pgvector_results = _pgvector_candidates(db, embedding, threshold, problem.id)
    if pgvector_results:
        return pgvector_results

    # --- Path 2: Token-overlap fallback ---
    # Bounded scan: full-table .all() loads every row + embedding into memory
    # and turns O(1) submit into O(N). Cap to 500 recent open/validated rows
    # and select only text columns needed for Jaccard.
    candidates = (
        db.query(Problem.id, Problem.title, Problem.description, Problem.address)
        .filter(Problem.status.in_([ProblemStatusEnum.OPEN, ProblemStatusEnum.VALIDATED]))
        .filter(Problem.id != problem.id)
        .order_by(Problem.created_at.desc())
        .limit(500)
        .all()
    )
    results = []
    for cand_id, cand_title, cand_desc, cand_addr in candidates:
        cand_text = f"{cand_title} {cand_desc}"
        sim = _token_overlap(text_content, cand_text)
        same_district = bool(
            problem.address
            and cand_addr
            and problem.address.strip().lower() == cand_addr.strip().lower()
        )
        effective_threshold = threshold - (0.15 if same_district else 0.0)
        if sim >= effective_threshold:
            results.append({
                "problem_id": cand_id,
                "title": cand_title,
                "similarity": round(sim, 4),
                "method": "jaccard_token",
            })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results
