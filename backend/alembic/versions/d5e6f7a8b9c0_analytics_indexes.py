"""indexes for government dashboard analytics queries

Revision ID: d5e6f7a8b9c0
Revises: 54bf0cd773ad
Create Date: 2026-09-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = '54bf0cd773ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Problems: time + category are grouped/filtered for monthly & category trends.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_problems_created_at "
        "ON problems (created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_problems_ai_category_created_at "
        "ON problems (ai_category, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_problems_ai_priority "
        "ON problems (ai_priority)"
    )
    # Collaborations: stage is grouped for the radar chart, industry_id drives leaderboards.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_collaborations_stage "
        "ON collaborations (stage)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_collaborations_industry_id "
        "ON collaborations (industry_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_collaborations_proposal_id "
        "ON collaborations (proposal_id)"
    )
    # Social impact reports: joined to collaborations for the reports page.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_social_impact_reports_collaboration_id "
        "ON social_impact_reports (collaboration_id)"
    )
    # University leaderboard: member counts are grouped by university.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_university_members_university_id "
        "ON university_members (university_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_university_members_university_id")
    op.execute("DROP INDEX IF EXISTS ix_social_impact_reports_collaboration_id")
    op.execute("DROP INDEX IF EXISTS ix_collaborations_proposal_id")
    op.execute("DROP INDEX IF EXISTS ix_collaborations_industry_id")
    op.execute("DROP INDEX IF EXISTS ix_collaborations_stage")
    op.execute("DROP INDEX IF EXISTS ix_problems_ai_priority")
    op.execute("DROP INDEX IF EXISTS ix_problems_ai_category_created_at")
    op.execute("DROP INDEX IF EXISTS ix_problems_created_at")