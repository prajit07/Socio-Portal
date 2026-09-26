"""add solution review & forward-to-industry trail

Revision ID: c1d2e3f4a5b6
Revises: b1e2f3a4c5d6
Create Date: 2026-09-26 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b1e2f3a4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'FORWARDED' to the native PG enum used for solution status.
    # SQLAlchemy persists the enum member NAME, so existing values are uppercase.
    # PG12+ allows ALTER TYPE ... ADD VALUE inside a transaction as long as the
    # new value is not used before commit — this migration does not insert rows.
    op.execute("ALTER TYPE solution_status_enum ADD VALUE IF NOT EXISTS 'FORWARDED'")

    op.add_column(
        'solutions',
        sa.Column('approved_by', sa.String(length=20), nullable=True),
    )
    op.add_column(
        'solutions',
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'solutions',
        sa.Column('forwarded_to_industry_id', sa.String(length=20), nullable=True),
    )
    op.add_column(
        'solutions',
        sa.Column('forwarded_by', sa.String(length=20), nullable=True),
    )
    op.add_column(
        'solutions',
        sa.Column('forwarded_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key('fk_solutions_forwarded_industry', 'solutions', 'industries', ['forwarded_to_industry_id'], ['id'])
    op.create_foreign_key('fk_solutions_forwarded_by', 'solutions', 'users', ['forwarded_by'], ['id'])
    op.create_foreign_key('fk_solutions_approved_by', 'solutions', 'users', ['approved_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_solutions_approved_by', 'solutions', type_='foreignkey')
    op.drop_constraint('fk_solutions_forwarded_by', 'solutions', type_='foreignkey')
    op.drop_constraint('fk_solutions_forwarded_industry', 'solutions', type_='foreignkey')
    op.drop_column('solutions', 'forwarded_at')
    op.drop_column('solutions', 'forwarded_by')
    op.drop_column('solutions', 'forwarded_to_industry_id')
    op.drop_column('solutions', 'approved_at')
    op.drop_column('solutions', 'approved_by')
    # Note: ALTER TYPE ... DROP VALUE is not implemented on Neon/PG for this
    # enum, so the 'FORWARDED' label is intentionally left in place on downgrade.