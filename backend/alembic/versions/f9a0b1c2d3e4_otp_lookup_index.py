"""composite index for OTP cooldown + verify lookups

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f9a0b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_otp_identifier_purpose_created "
        "ON otp (identifier, purpose, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_otp_expires_at "
        "ON otp (expires_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_otp_expires_at")
    op.execute("DROP INDEX IF EXISTS ix_otp_identifier_purpose_created")
