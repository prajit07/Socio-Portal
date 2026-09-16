"""Routing engine — plan.txt §3 & §8.5.

Rule-based (not LLM):
  - ALL problems -> ALL universities (university_admin users; no tag filter)
  - Problem AI tags ∩ industry domain_tags -> notify industry (industries with no
    domain_tags also receive everything)
Creates a RoutingLog + Notification per matched solver.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import RoleEnum, RoutingTypeEnum, NotificationTypeEnum
from app.models.routing import RoutingLog, Notification
from app.models.user import User


def route_problem(db: Session, problem, ai_tag_ids: Optional[list[str]] = None) -> int:
    """Route a problem to matching solvers. Returns number of solvers notified."""
    ai_tags = set(ai_tag_ids or [])
    routed = 0
    seen = set()

    def notify(user_id: str, rtype: RoutingTypeEnum, reason: str):
        nonlocal routed
        if user_id in seen:
            return
        seen.add(user_id)
        db.add(RoutingLog(problem_id=problem.id, routed_to_type=rtype, routed_to_id=user_id, reason=reason))
        db.add(
            Notification(
                user_id=user_id,
                type=NotificationTypeEnum.PROBLEM_ROUTED,
                message=f"New problem routed to you: '{problem.title}'",
                reference_id=problem.id,
            )
        )
        routed += 1

    # 1. All universities see everything — select ids only, not full User rows.
    universities = db.query(User.id).filter(User.role == RoleEnum.UNIVERSITY_ADMIN).limit(2000).all()
    for (uid,) in universities:
        notify(uid, RoutingTypeEnum.UNIVERSITY, "HEI receives all problems")

    # 2. Tag-matched industries — fetch only id + domain_tags.
    industries = (
        db.query(User.id, User.domain_tags)
        .filter(User.role == RoleEnum.INDUSTRY)
        .limit(2000)
        .all()
    )
    for uid, dtags in industries:
        tags = set(dtags or [])
        if not tags or (tags & ai_tags):
            notify(uid, RoutingTypeEnum.INDUSTRY, "Domain tags matched problem AI tags")

    db.flush()
    return routed
