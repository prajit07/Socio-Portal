from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.problem import Problem, Solution
from app.models.org import University, Industry
from app.models.collaboration import Collaboration, SocialImpactReport
from app.models.evidence import Evidence
from app.models.routing import RoutingLog

router = APIRouter(prefix="/government", tags=["government"])


def _admin_or_gov(current_user: User):
    if current_user.role.value not in ("government", "admin"):
        raise HTTPException(status_code=403, detail="Government access only")


@router.get("/analytics", response_model=dict)
def analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Full analytics for government dashboard: KPIs, status/category/priority breakdowns,
    district-wise, monthly trends, completion rates, and impact summary."""
    _admin_or_gov(current_user)

    # ---- KPIs ----
    total = db.query(func.count(Problem.id)).scalar() or 0
    by_status = (
        db.query(Problem.status, func.count(Problem.id))
        .group_by(Problem.status)
        .all()
    )
    by_category = (
        db.query(Problem.ai_category, func.count(Problem.id))
        .filter(Problem.ai_category.isnot(None))
        .group_by(Problem.ai_category)
        .all()
    )
    by_priority = (
        db.query(Problem.ai_priority, func.count(Problem.id))
        .filter(Problem.ai_priority.isnot(None))
        .group_by(Problem.ai_priority)
        .all()
    )
    active_collab = db.query(func.count(Collaboration.id)).scalar() or 0
    proposals = db.query(func.count(Solution.id)).scalar() or 0
    universities = db.query(func.count(University.id)).scalar() or 0
    industries = db.query(func.count(Industry.id)).scalar() or 0

    def cnt(statuses):
        return sum(c for s, c in by_status if s.value in statuses) if by_status else 0

    resolved = cnt({"implemented", "closed"})
    open_count = cnt({"open", "validated", "in_review", "proposal_submitted"})
    duplicate_count = cnt({"duplicate"})
    rejected_count = cnt({"rejected"})

    # Completion rate
    completion_rate = round((resolved / total * 100), 1) if total else 0

    # ---- District-wise breakdown ----
    district_rows = (
        db.query(Problem.address, func.count(Problem.id))
        .filter(Problem.address.isnot(None), Problem.address != "")
        .group_by(Problem.address)
        .order_by(func.count(Problem.id).desc())
        .limit(20)
        .all()
    )
    # Extract district from address (heuristic: first comma-separated segment)
    district_map: dict[str, int] = {}
    for addr, cnt in district_rows:
        district = addr.split(",")[0].strip() if addr else "Unknown"
        district_map[district] = district_map.get(district, 0) + cnt
    by_district = sorted(
        [{"district": d, "count": c} for d, c in district_map.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:15]

    # ---- Monthly trends (last 12 months) ----
    now = datetime.now(timezone.utc)
    monthly = []
    for i in range(11, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month_end = now
        count = (
            db.query(func.count(Problem.id))
            .filter(Problem.created_at >= month_start, Problem.created_at < month_end)
            .scalar() or 0
        )
        monthly.append({
            "month": month_start.strftime("%b %Y"),
            "count": count,
        })

    # ---- Category trends (problems per category over last 6 months) ----
    cat_trends = []
    top_cats = [cat for cat, _ in sorted(by_category, key=lambda x: x[1], reverse=True)[:6]]
    for cat_name in top_cats:
        data_points = []
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                month_end = now
            count = (
                db.query(func.count(Problem.id))
                .filter(
                    Problem.ai_category == cat_name,
                    Problem.created_at >= month_start,
                    Problem.created_at < month_end,
                )
                .scalar() or 0
            )
            data_points.append({"month": month_start.strftime("%b"), "count": count})
        cat_trends.append({"category": cat_name, "data": data_points})

    # ---- Priority distribution ----
    priority_dist = [{"priority": (p.value if p else "none"), "count": c} for p, c in by_priority]

    # ---- Impact reports summary ----
    total_beneficiaries = db.query(func.coalesce(func.sum(SocialImpactReport.beneficiaries_count), 0)).scalar()
    impact_count = db.query(func.count(SocialImpactReport.id)).scalar() or 0

    # ---- Active collaboration stages ----
    collab_stages = (
        db.query(Collaboration.stage, func.count(Collaboration.id))
        .group_by(Collaboration.stage)
        .all()
    )
    by_stage = [{"stage": s, "count": c} for s, c in collab_stages]

    return {
        "kpis": {
            "total_problems": total,
            "resolved": resolved,
            "open": open_count,
            "duplicates": duplicate_count,
            "rejected": rejected_count,
            "active_collaborations": active_collab,
            "proposals": proposals,
            "universities": universities,
            "industries": industries,
            "completion_rate": completion_rate,
            "total_beneficiaries": total_beneficiaries,
            "impact_reports": impact_count,
        },
        "by_status": [{"status": s.value, "count": c} for s, c in by_status],
        "by_category": [{"category": cat, "count": c} for cat, c in by_category],
        "by_priority": priority_dist,
        "by_district": by_district,
        "monthly_trends": monthly,
        "category_trends": cat_trends,
        "collaboration_stages": by_stage,
    }


@router.get("/leaderboards", response_model=dict)
def leaderboards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.value not in ("government", "admin"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=403, detail="Government access only")

    unis = db.query(University.id, University.name, University.verified).order_by(University.name).all()
    inds = db.query(Industry.id, Industry.name, Industry.verified).order_by(Industry.name).all()
    return {
        "universities": [{"id": u.id, "name": u.name, "verified": u.verified} for u in unis],
        "industries": [{"id": i.id, "name": i.name, "verified": i.verified} for i in inds],
    }


@router.get("/impact-reports", response_model=list)
def impact_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return all social impact reports enriched with collaboration, proposal, and industry info.
    Used by the Government Impact Reports page for display and CSV/PDF export.
    """
    _admin_or_gov(current_user)

    from app.models.problem import Solution
    reports = (
        db.query(SocialImpactReport)
        .order_by(SocialImpactReport.reported_at.desc())
        .all()
    )
    result = []
    for r in reports:
        collab = db.get(Collaboration, r.collaboration_id)
        proposal = db.get(Solution, collab.proposal_id) if collab else None
        industry = db.get(Industry, collab.industry_id) if collab else None
        result.append({
            "id": r.id,
            "reported_at": r.reported_at.isoformat() if r.reported_at else None,
            "beneficiaries_count": r.beneficiaries_count,
            "impact_summary": r.impact_summary,
            "district": r.district,
            "state": r.state,
            "collaboration_id": r.collaboration_id,
            "collaboration_stage": collab.stage if collab else None,
            "proposal_title": proposal.title if proposal else None,
            "proposal_id": proposal.id if proposal else None,
            "industry_name": industry.name if industry else None,
            "industry_type": industry.type if industry else None,
        })
    return result

