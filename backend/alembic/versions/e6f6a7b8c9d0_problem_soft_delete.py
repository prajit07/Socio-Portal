"""soft-delete columns for problems (deletion reason)

Revision ID: e6f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-28 17:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'e6f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('problems', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('problems', sa.Column('deletion_reason', sa.Text(), nullable=True))
    op.add_column('problems', sa.Column('deleted_by_id', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('problems', 'deleted_by_id')
    op.drop_column('problems', 'deletion_reason')
    op.drop_column('problems', 'deleted_at')
