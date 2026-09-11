import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.problem import Problem, Solution
from app.models.org import University, Industry, UniversityMember
from app.models.collaboration import Collaboration, SocialImpactReport
from app.models.evidence import Evidence
from app.models.routing import RoutingLog

router = APIRouter(prefix="/government", tags=["government"])

# Aggregates are computed from slowly-changing data. A short TTL cache makes
# repeated loads (page navigation, refresh) near-instant on a remote DB where
# each round trip adds latency. Invalidation happens naturally via the TTL.
AGGREGATE_CACHE_TTL = 30  # seconds
_aggregate_cache: dict[str, tuple[float, object]] = {}
_aggregate_cache_lock = threading.Lock()


def _admin_or_gov(current_user: User):
    if current_user.role.value not in ("government", "admin"):
        raise HTTPException(status_code=403, detail="Government access only")


def _cached(key: str, producer):
    """Return cached value if fresh, otherwise compute, store and return."""
    now = time.monotonic()
    with _aggregate_cache_lock:
        hit = _aggregate_cache.get(key)
        if hit and hit[0] > now:
            return hit[1]
    value = producer()
    with _aggregate_cache_lock:
        _aggregate_cache[key] = (now + AGGREGATE_CACHE_TTL, value)
    return value


def _month_range(now: datetime, months_back: int):
    """Return (start, end) datetime for an exact calendar month, `months_back` months before `now`."""
    year = now.year
    month = now.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    end_year = year
    end_month = month - 1
    while end_month <= 0:
        end_month += 12
        end_year -= 1
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if months_back == 0:
        end = now
    else:
        end = datetime(end_year, end_month, 1, tzinfo=timezone.utc)
    return start, end


def _compute_analytics(db: Session) -> dict:
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
    district_map: dict[str, int] = {}
    for addr, cnt in district_rows:
        district = addr.split(",")[0].strip() if addr else "Unknown"
        district_map[district] = district_map.get(district, 0) + cnt
    by_district = sorted(
        [{"district": d, "count": c} for d, c in district_map.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:15]

    # ---- Monthly trends (last 12 calendar months) — ONE grouped query ----
    now = datetime.now(timezone.utc)
    month_start_12, _ = _month_range(now, 11)
    month_rows = (
        db.query(
            extract("year", Problem.created_at).label("yr"),
            extract("month", Problem.created_at).label("mo"),
            func.count(Problem.id),
        )
        .filter(Problem.created_at >= month_start_12, Problem.created_at < now)
        .group_by(extract("year", Problem.created_at), extract("month", Problem.created_at))
        .all()
    )
    monthly_counts: dict[str, int] = {}
    for yr, mo, cnt in month_rows:
        monthly_counts[f"{int(yr):04d}-{int(mo):02d}"] = cnt
    monthly = []
    for i in range(11, -1, -1):
        start, _ = _month_range(now, i)
        monthly.append({
            "month": start.strftime("%b %Y"),
            "count": monthly_counts.get(start.strftime("%Y-%m"), 0),
        })

    # ---- Category trends (problems per category over last 6 calendar months) ----
    top_cats = [cat for cat, _ in sorted(by_category, key=lambda x: x[1], reverse=True)[:6]]
    cat_trends = []
    if top_cats:
        cat_start, _ = _month_range(now, 5)
        rows = (
            db.query(
                Problem.ai_category,
                extract("year", Problem.created_at).label("yr"),
                extract("month", Problem.created_at).label("mo"),
                func.count(Problem.id),
            )
            .filter(
                Problem.ai_category.in_(top_cats),
                Problem.created_at >= cat_start,
            )
            .group_by(Problem.ai_category, extract("year", Problem.created_at), extract("month", Problem.created_at))
            .all()
        )
        bucket_map: dict[str, dict[str, int]] = {}
        for cat, yr, mo, cnt in rows:
            key = f"{int(yr):04d}-{int(mo):02d}"
            bucket_map.setdefault(cat, {})[key] = cnt

        for cat_name in top_cats:
            cat_buckets = bucket_map.get(cat_name, {})
            if not cat_buckets:
                continue
            data_points = []
            for i in range(5, -1, -1):
                start, _ = _month_range(now, i)
                data_points.append({
                    "month": start.strftime("%b"),
                    "count": cat_buckets.get(start.strftime("%Y-%m"), 0),
                })
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


@router.get("/analytics", response_model=dict)
def analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Full analytics for government dashboard: KPIs, status/category/priority breakdowns,
    district-wise, monthly trends, completion rates, and impact summary."""
    _admin_or_gov(current_user)
    return _cached("analytics", lambda: _compute_analytics(db))


@router.get("/leaderboards", response_model=dict)
def leaderboards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.value not in ("government", "admin"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=403, detail="Government access only")

    def _compute():
        # Rank industries by number of collaborations held (a real activity metric).
        ind_rows = (
            db.query(
                Industry.id,
                Industry.name,
                Industry.verified,
                Industry.type,
                func.count(Collaboration.id).label("collab_count"),
            )
            .outerjoin(Collaboration, Collaboration.industry_id == Industry.id)
            .group_by(Industry.id, Industry.name, Industry.verified, Industry.type)
            .order_by(func.count(Collaboration.id).desc(), Industry.name)
            .limit(25)
            .all()
        )
        # Rank universities by number of members (proxy for institutional engagement).
        uni_rows = (
            db.query(
                University.id,
                University.name,
                University.verified,
                func.count(UniversityMember.id).label("member_count"),
            )
            .outerjoin(UniversityMember, UniversityMember.university_id == University.id)
            .group_by(University.id, University.name, University.verified)
            .order_by(func.count(UniversityMember.id).desc(), University.name)
            .limit(25)
            .all()
        )
        return {
            "universities": [
                {"id": u.id, "name": u.name, "verified": u.verified, "member_count": u.member_count}
                for u in uni_rows
            ],
            "industries": [
                {
                    "id": i.id,
                    "name": i.name,
                    "verified": i.verified,
                    "type": i.type,
                    "collaboration_count": i.collab_count,
                }
                for i in ind_rows
            ],
        }

    return _cached("leaderboards", _compute)


@router.get("/impact-reports", response_model=list)
def impact_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return all social impact reports enriched with collaboration, proposal, and industry info.
    Used by the Government Impact Reports page for display and CSV/PDF export.
    """
    _admin_or_gov(current_user)

    def _compute():
        # Single joined query — no per-row lookups (kills the N+1 pattern).
        rows = (
            db.query(
                SocialImpactReport.id,
                SocialImpactReport.reported_at,
                SocialImpactReport.beneficiaries_count,
                SocialImpactReport.impact_summary,
                SocialImpactReport.district,
                SocialImpactReport.state,
                SocialImpactReport.collaboration_id,
                Collaboration.stage.label("collaboration_stage"),
                Solution.title.label("proposal_title"),
                Solution.id.label("proposal_id"),
                Industry.name.label("industry_name"),
                Industry.type.label("industry_type"),
            )
            .outerjoin(Collaboration, Collaboration.id == SocialImpactReport.collaboration_id)
            .outerjoin(Solution, Solution.id == Collaboration.proposal_id)
            .outerjoin(Industry, Industry.id == Collaboration.industry_id)
            .order_by(SocialImpactReport.reported_at.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
                "beneficiaries_count": r.beneficiaries_count,
                "impact_summary": r.impact_summary,
                "district": r.district,
                "state": r.state,
                "collaboration_id": r.collaboration_id,
                "collaboration_stage": r.collaboration_stage,
                "proposal_title": r.proposal_title,
                "proposal_id": r.proposal_id,
                "industry_name": r.industry_name,
                "industry_type": r.industry_type,
            }
            for r in rows
        ]

    return _cached("impact_reports", _compute)