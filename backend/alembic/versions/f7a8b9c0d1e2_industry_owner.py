"""link industry profiles to their owning user

Revision ID: f7a8b9c0d1e2
Revises: e6f6a7b8c9d0
Create Date: 2026-08-28 21:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('industries', sa.Column('created_by', sa.String(length=20), nullable=True))
    op.create_foreign_key('fk_industries_created_by', 'industries', 'users', ['created_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_industries_created_by', 'industries', type_='foreignkey')
    op.drop_column('industries', 'created_by')
