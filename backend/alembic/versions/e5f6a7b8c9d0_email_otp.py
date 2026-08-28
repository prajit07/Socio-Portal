"""email verification + otp table

Revision ID: e5f6a7b8c9d0
Revises: 877c640c9f15
Create Date: 2026-08-27 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = '877c640c9f15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        'otp',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('purpose', sa.String(length=20), nullable=False),
        sa.Column('code_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_otp_identifier', 'otp', ['identifier'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_otp_identifier', table_name='otp')
    op.drop_table('otp')
    op.drop_column('users', 'is_email_verified')
