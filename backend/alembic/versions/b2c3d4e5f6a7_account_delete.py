"""allow safe account self-deletion: make owner FKs nullable

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-28 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Owner FKs are set to NULL (orphaning the content) when a user deletes
    # their account, instead of cascading a destructive delete across the
    # whole problem/solution/team graph.
    op.alter_column('problems', 'submitter_id',
                    existing_type=sa.String(length=20), nullable=True)
    op.alter_column('solutions', 'author_id',
                    existing_type=sa.String(length=20), nullable=True)
    op.alter_column('teams', 'created_by',
                    existing_type=sa.String(length=20), nullable=True)


def downgrade() -> None:
    op.alter_column('teams', 'created_by',
                    existing_type=sa.String(length=20), nullable=False)
    op.alter_column('solutions', 'author_id',
                    existing_type=sa.String(length=20), nullable=False)
    op.alter_column('problems', 'submitter_id',
                    existing_type=sa.String(length=20), nullable=False)
