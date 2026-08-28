"""phase 4-7 schema: orgs, teams, proposals, collaborations, engagement

Revision ID: a1b2c3d4e5f6
Revises: e5f6a7b8c9d0
Create Date: 2026-08-27 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- referenced-by-many orgs first ---
    op.create_table(
        'universities',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('registration_no', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'industries',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=40), nullable=True),
        sa.Column('registration_no', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('domain_tags', sa.JSON(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- teams (refs universities/problems/users) ---
    op.create_table(
        'teams',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('problem_id', sa.String(length=20), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('university_id', sa.String(length=20), sa.ForeignKey('universities.id'), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('created_by', sa.String(length=20), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- link proposals (solutions) to teams ---
    op.add_column(
        'solutions',
        sa.Column('team_id', sa.String(length=20), sa.ForeignKey('teams.id'), nullable=True),
    )

    op.create_table(
        'university_members',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('university_id', sa.String(length=20), sa.ForeignKey('universities.id'), nullable=False),
        sa.Column('user_id', sa.String(length=20), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('member_role', sa.String(length=20), nullable=False, server_default='student'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'team_members',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('team_id', sa.String(length=20), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('user_id', sa.String(length=20), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(length=40), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- collaborations (refs solutions + industries) ---
    op.create_table(
        'collaborations',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('proposal_id', sa.String(length=20), sa.ForeignKey('solutions.id'), nullable=False),
        sa.Column('industry_id', sa.String(length=20), sa.ForeignKey('industries.id'), nullable=False),
        sa.Column('stage', sa.String(length=20), nullable=False, server_default='interested'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'milestones',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('collaboration_id', sa.String(length=20), sa.ForeignKey('collaborations.id'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'deliverables',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('milestone_id', sa.String(length=20), sa.ForeignKey('milestones.id'), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ip_records',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('collaboration_id', sa.String(length=20), sa.ForeignKey('collaborations.id'), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('reference_no', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'social_impact_reports',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('collaboration_id', sa.String(length=20), sa.ForeignKey('collaborations.id'), nullable=False),
        sa.Column('beneficiaries_count', sa.Integer(), nullable=True),
        sa.Column('impact_summary', sa.Text(), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('reported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'comments',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('entity_id', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.String(length=20), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'upvotes',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('problem_id', sa.String(length=20), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('user_id', sa.String(length=20), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('problem_id', 'user_id', name='uq_upvote_problem_user'),
    )

    op.create_table(
        'citizen_profiles',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.String(length=20), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.String(length=20), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=40), nullable=True),
        sa.Column('entity_id', sa.String(length=20), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('citizen_profiles')
    op.drop_table('upvotes')
    op.drop_table('comments')
    op.drop_table('social_impact_reports')
    op.drop_table('ip_records')
    op.drop_table('deliverables')
    op.drop_table('milestones')
    op.drop_table('collaborations')
    op.drop_table('team_members')
    op.drop_column('solutions', 'team_id')
    op.drop_table('teams')
    op.drop_table('university_members')
    op.drop_table('industries')
    op.drop_table('universities')
