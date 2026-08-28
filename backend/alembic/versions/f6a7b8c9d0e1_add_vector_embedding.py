"""Add pgvector embedding column to problems table.

Revision ID: f6a7b8c9d0e1
Revises: a1b2c3d4e5f6
Create Date: 2026-08-28 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgresql() -> bool:
    """Check if the current engine is PostgreSQL."""
    try:
        bind = op.get_bind()
        return bind.dialect.name == "postgresql"
    except Exception:
        return False


def upgrade() -> None:
    """Add 384-dim embedding column for pgvector semantic duplicate detection."""
    if not _is_postgresql():
        # SQLite does not support pgvector; skip silently.
        return

    # Ensure pgvector extension is available
    op.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    # Add the embedding column — nullable so existing rows are unaffected
    op.execute(text("ALTER TABLE problems ADD COLUMN IF NOT EXISTS embedding vector(384);"))

    # Create an approximate IVFFlat index for cosine similarity lookups
    # (requires at least ~100 rows to be useful; fails silently if table is empty at migration time)
    try:
        op.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_problems_embedding "
            "ON problems USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
        ))
    except Exception:
        pass  # Index creation is advisory; not fatal


def downgrade() -> None:
    """Remove embedding column."""
    if not _is_postgresql():
        return
    op.execute(text("DROP INDEX IF EXISTS ix_problems_embedding;"))
    op.execute(text("ALTER TABLE problems DROP COLUMN IF EXISTS embedding;"))
