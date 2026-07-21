"""add auditable controlled AI analysis records

Revision ID: a9d0e1f2a3b4
Revises: a8c9d0e1f2a3
Create Date: 2026-07-21 07:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'a9d0e1f2a3b4'
down_revision = 'a8c9d0e1f2a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if 'ai_analysis_records' in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        'ai_analysis_records',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('analysis_type', sa.String(length=40), nullable=False),
        sa.Column('target_type', sa.String(length=40), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('traceability_id', sa.String(length=100), nullable=True),
        sa.Column('engine', sa.String(length=100), nullable=False, server_default='guarded-heuristic-v1'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='completed'),
        sa.Column('input_redacted', sa.JSON(), nullable=False),
        sa.Column('output', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_ai_analysis_records_user_created', 'ai_analysis_records', ['user_id', 'created_at'])
    op.create_index('idx_ai_analysis_records_target', 'ai_analysis_records', ['target_type', 'target_id'])
    op.create_index('ix_ai_analysis_records_user_id', 'ai_analysis_records', ['user_id'])
    op.create_index('ix_ai_analysis_records_traceability_id', 'ai_analysis_records', ['traceability_id'])


def downgrade() -> None:
    bind = op.get_bind()
    if 'ai_analysis_records' in set(sa.inspect(bind).get_table_names()):
        op.drop_table('ai_analysis_records')
