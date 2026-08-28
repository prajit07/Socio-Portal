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
from app.services import ai_categorization, duplicate_detection, routing_engine
from app.services.duplicate_detection import generate_embedding, _PGVECTOR_AVAILABLE


def run_analysis(db: Session, problem: Problem) -> dict:
    # Idempotent: clear prior AI-derived rows for this problem
    db.query(ProblemTag).filter(ProblemTag.problem_id == problem.id).delete()
    db.query(RoutingLog).filter(RoutingLog.problem_id == problem.id).delete()
    db.flush()

    result = ai_categorization.categorize(
        problem.title, problem.description, problem.evidence_text, problem.tags
    )

    problem.ai_category = result["category_name"]
    problem.ai_tags = [t["id"] for t in result["tags"]]
    problem.ai_priority = result["priority"]

    # Generate and store embedding for pgvector duplicate detection
    if _PGVECTOR_AVAILABLE:
        try:
            text_content = f"{problem.title} {problem.description} {problem.evidence_text or ''}"
            embedding = generate_embedding(text_content)
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
