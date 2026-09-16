"""indexes for problem list filters (status, submitter, assignee, soft-delete)

Revision ID: e8f9a0b1c2d3
Revises: d5e6f7a8b9c0
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_problems_status_created "
        "ON problems (status, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_problems_submitter_created "
        "ON problems (submitter_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_problems_assigned_to "
        "ON problems (assigned_to_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_problems_deleted_at "
        "ON problems (deleted_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_problems_deleted_at")
    op.execute("DROP INDEX IF EXISTS ix_problems_assigned_to")
    op.execute("DROP INDEX IF EXISTS ix_problems_submitter_created")
    op.execute("DROP INDEX IF EXISTS ix_problems_status_created")
