"""collaboration engagement_type + funding/testing/startup + ip file attachment

Revision ID: b1e2f3a4c5d6
Revises: f101b5ced202
Create Date: 2026-09-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1e2f3a4c5d6'
down_revision: Union[str, Sequence[str], None] = 'f9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'collaborations',
        sa.Column('engagement_type', sa.String(length=20), nullable=False, server_default='express_interest'),
    )
    op.add_column(
        'collaborations',
        sa.Column('funding_status', sa.String(length=20), nullable=True),
    )
    op.add_column(
        'collaborations',
        sa.Column('testing_outcomes', sa.Text(), nullable=True),
    )
    op.add_column(
        'collaborations',
        sa.Column('startup_created', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'ip_records',
        sa.Column('file_url', sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('ip_records', 'file_url')
    op.drop_column('collaborations', 'startup_created')
    op.drop_column('collaborations', 'testing_outcomes')
    op.drop_column('collaborations', 'funding_status')
    op.drop_column('collaborations', 'engagement_type')