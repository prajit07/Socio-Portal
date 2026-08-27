"""Duplicate detection.

Plan.txt §8.4: generate embeddings for each new problem, vector-similarity search
(pgvector) against existing OPEN problems in the same district, flag if similarity
> threshold.

Without a configured embedding provider we use a deterministic token-overlap
(Jaccard) similarity as a stand-in. Swap `similarity()` for a pgvector query when
an embedding backend is available.
"""
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.enums import ProblemStatusEnum

THRESHOLD = 0.6


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def find_duplicates(db: Session, problem: Problem, threshold: float = THRESHOLD):
    """Return list of {problem_id, title, similarity} for likely duplicates (same district preferred)."""
    candidates = (
        db.query(Problem)
        .filter(Problem.status == ProblemStatusEnum.OPEN)
        .filter(Problem.id != problem.id)
        .all()
    )
    new_text = f"{problem.title} {problem.description}"
    results = []
    for cand in candidates:
        sim = similarity(new_text, f"{cand.title} {cand.description}")
        same_district = bool(problem.address and cand.address and problem.address == cand.address)
        if sim >= threshold or (same_district and sim >= threshold - 0.15):
            results.append({"problem_id": cand.id, "title": cand.title, "similarity": round(sim, 3)})
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results
