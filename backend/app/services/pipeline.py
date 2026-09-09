"""End-to-end AI pipeline for a problem (plan.txt §3 & §8).

Submitted problem
  -> AI validation / categorization + priority (ai_categorization)
  -> duplicate detection (duplicate_detection)
  -> routing engine (routing_engine)
Mutates the problem status and persists tags, routing logs and notifications.
"""
from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.tag import Tag, ProblemTag
from app.models.routing import RoutingLog
from app.models.enums import ProblemStatusEnum, NotificationTypeEnum
from app.models.routing import Notification
from app.models.classification_feedback import ClassificationFeedback
from app.core.config import settings
from app.services import ai_categorization, duplicate_detection, routing_engine


def _log_lora_shadow(db: Session, problem: Problem, result: dict):
    """Phase 2 shadow mode: record baseline-vs-LoRA disagreement for cutover metrics.
    Guarded: never breaks the pipeline. Uses submitter as the feedback author.
    Idempotent: prior shadow rows for this problem are replaced on re-analysis,
    mirroring the ProblemTag/RoutingLog cleanup in run_analysis."""
    try:
        shadow = (result or {}).get("_lora_shadow") or {}
        if not (settings.lora_enabled and shadow.get("lora_available")):
            return
        db.query(ClassificationFeedback).filter(
            ClassificationFeedback.problem_id == problem.id,
            ClassificationFeedback.notes.startswith("lora-shadow"),
        ).delete()
        tag_ids = [t["id"] for t in (result.get("tags") or [])
                   if isinstance(t, dict) and t.get("id")]
        db.add(ClassificationFeedback(
            problem_id=problem.id,
            ai_category_id=result.get("category_id"),
            ai_category_name=result.get("category_name"),
            ai_tags=tag_ids,
            ai_priority=result.get("priority").value if result.get("priority") else None,
            corrected_category_id=shadow.get("lora") or result.get("category_id"),
            corrected_category_name=shadow.get("lora") or result.get("category_name"),
            user_id=problem.submitter_id,
            is_correction=not shadow.get("agree", True),
            notes=f"lora-shadow agree={shadow.get('agree')} label10={shadow.get('label10')} "
                  f"lossy={shadow.get('lossy_map')} baseline={shadow.get('baseline')}",
        ))
        db.flush()
    except Exception:
        pass


def run_analysis(db: Session, problem: Problem) -> dict:
    # Idempotent: clear prior AI-derived rows for this problem
    db.query(ProblemTag).filter(ProblemTag.problem_id == problem.id).delete()
    db.query(RoutingLog).filter(RoutingLog.problem_id == problem.id).delete()
    db.flush()

    result = ai_categorization.categorize(
        problem.title, problem.description, problem.evidence_text, problem.tags
    )
    _log_lora_shadow(db, problem, result)

    problem.ai_category = result["category_name"]
    problem.ai_tags = [t["id"] for t in result["tags"]]
    problem.ai_priority = result["priority"]

    # Generate and store embedding for pgvector duplicate detection.
    # Skipped entirely when the column is absent (e.g. Clever Cloud with
    # PGVECTOR_ENABLED=False) — assignment would otherwise poison the later
    # flush/commit. Also avoids a wasted embedding API call per submission.
    if duplicate_detection.embedding_supported(db):
        try:
            text_content = f"{problem.title} {problem.description} {problem.evidence_text or ''}"
            embedding = duplicate_detection.generate_embedding(text_content)
            problem.embedding = embedding
        except Exception:
            pass  # Non-critical: duplicate detection falls back to Jaccard

    # Deduplicate by tag ID — keep highest confidence for each tag.
    # The AI model can return the same tag_id more than once (e.g. from
    # overlapping keyword lists), which would violate the uq_problem_tag
    # unique constraint on (problem_id, tag_id).
    seen_tag_ids: dict[str, dict] = {}
    for t in result["tags"]:
        tid = t["id"]
        if tid not in seen_tag_ids or (t.get("confidence") or 0) > (seen_tag_ids[tid].get("confidence") or 0):
            seen_tag_ids[tid] = t

    # Persist AI tags with confidence
    inserted_tag_ids = set()
    for t in seen_tag_ids.values():
        tag = db.query(Tag).filter(Tag.id == t["id"]).first()
        if not tag:
            tag = db.query(Tag).filter(Tag.name == t["name"]).first()
        if not tag:
            tag = Tag(id=t["id"], name=t["name"])
            db.add(tag)
            db.flush()
            
        if tag.id not in inserted_tag_ids:
            db.add(ProblemTag(problem_id=problem.id, tag_id=tag.id, confidence=t.get("confidence")))
            inserted_tag_ids.add(tag.id)

    # Duplicate detection
    dups = duplicate_detection.find_duplicates(db, problem)
    if dups:
        best = dups[0]
        problem.ai_duplicate_check = True
        problem.ai_duplicate_of = best["problem_id"]
        problem.status = ProblemStatusEnum.DUPLICATE
        sub = db.query(Problem).filter(Problem.id == problem.submitter_id).first()
        if sub:
            db.add(
                Notification(
                    user_id=problem.submitter_id,
                    type=NotificationTypeEnum.DUPLICATE_FLAGGED,
                    message=f"Your problem may be a duplicate of '{best['title']}'.",
                    reference_id=problem.id,
                )
            )
    else:
        problem.ai_duplicate_check = False
        problem.status = ProblemStatusEnum.OPEN  # validated + opened

    db.flush()

    # Routing engine
    routed = routing_engine.route_problem(db, problem, [t["id"] for t in result["tags"]])
    db.commit()
    db.refresh(problem)

    return {
        "problem_id": problem.id,
        "category_id": result["category_id"],
        "category_name": result["category_name"],
        "tags": result["tags"],
        "priority": result["priority"].value,
        "duplicates": dups,
        "routed_count": routed,
        "status": problem.status.value,
    }
