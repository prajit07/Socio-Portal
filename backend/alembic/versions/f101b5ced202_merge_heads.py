"""merge heads

Revision ID: f101b5ced202
Revises: f6a7b8c9d0e1, f7a8b9c0d1e2
Create Date: 2026-09-03 19:38:58.494016

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f101b5ced202'
down_revision: Union[str, Sequence[str], None] = ('f6a7b8c9d0e1', 'f7a8b9c0d1e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
