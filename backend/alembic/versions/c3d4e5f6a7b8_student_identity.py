"""add student identity (department, roll_number) to university_members

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-28 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('university_members', sa.Column('department', sa.String(length=100), nullable=True))
    op.add_column('university_members', sa.Column('roll_number', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('university_members', 'roll_number')
    op.drop_column('university_members', 'department')
