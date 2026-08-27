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

    def notify(user, rtype: RoutingTypeEnum, reason: str):
        nonlocal routed
        if user.id in seen:
            return
        seen.add(user.id)
        db.add(RoutingLog(problem_id=problem.id, routed_to_type=rtype, routed_to_id=user.id, reason=reason))
        db.add(
            Notification(
                user_id=user.id,
                type=NotificationTypeEnum.PROBLEM_ROUTED,
                message=f"New problem routed to you: '{problem.title}'",
                reference_id=problem.id,
            )
        )
        routed += 1

    # 1. All universities see everything
    universities = db.query(User).filter(User.role == RoleEnum.UNIVERSITY_ADMIN).all()
    for u in universities:
        notify(u, RoutingTypeEnum.UNIVERSITY, "HEI receives all problems")

    # 2. Tag-matched industries
    industries = db.query(User).filter(User.role == RoleEnum.INDUSTRY).all()
    for u in industries:
        tags = set(u.domain_tags or [])
        if not tags or (tags & ai_tags):
            notify(u, RoutingTypeEnum.INDUSTRY, "Domain tags matched problem AI tags")

    db.flush()
    return routed
