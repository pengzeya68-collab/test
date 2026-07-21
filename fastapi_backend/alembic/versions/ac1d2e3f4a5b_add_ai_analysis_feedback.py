"""add human feedback for controlled AI analysis

Revision ID: ac1d2e3f4a5b
Revises: ab1c2d3e4f5a
Create Date: 2026-07-22 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'ac1d2e3f4a5b'
down_revision = 'ab1c2d3e4f5a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if 'test_scenarios' in tables:
        columns = {column['name'] for column in sa.inspect(bind).get_columns('test_scenarios')}
        additions = (
            ('schedule_cron_expression', sa.Column('schedule_cron_expression', sa.String(length=200), nullable=True)),
            ('schedule_env_id', sa.Column('schedule_env_id', sa.Integer(), nullable=True)),
            ('schedule_webhook_url', sa.Column('schedule_webhook_url', sa.Text(), nullable=True)),
            ('schedule_task_name', sa.Column('schedule_task_name', sa.String(length=200), nullable=True)),
            ('schedule_is_active', sa.Column('schedule_is_active', sa.Boolean(), nullable=True, server_default=sa.true())),
        )
        for name, column in additions:
            if name not in columns:
                op.add_column('test_scenarios', column)

    if 'ai_analysis_feedback' not in tables:
        op.create_table(
            'ai_analysis_feedback',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column(
                'analysis_id',
                sa.String(length=32),
                sa.ForeignKey('ai_analysis_records.id', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('analysis_type', sa.String(length=40), nullable=False),
            sa.Column('predicted_category', sa.String(length=40), nullable=True),
            sa.Column('accepted', sa.Boolean(), nullable=False),
            sa.Column('corrected_category', sa.String(length=40), nullable=True),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint('analysis_id', 'user_id', name='uq_ai_analysis_feedback_user'),
        )
        op.create_index('ix_ai_analysis_feedback_id', 'ai_analysis_feedback', ['id'])
        op.create_index('ix_ai_analysis_feedback_user_id', 'ai_analysis_feedback', ['user_id'])
        op.create_index('idx_ai_analysis_feedback_user_created', 'ai_analysis_feedback', ['user_id', 'created_at'])
        op.create_index('idx_ai_analysis_feedback_type', 'ai_analysis_feedback', ['analysis_type'])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if 'ai_analysis_feedback' in tables:
        op.drop_table('ai_analysis_feedback')
    if 'test_scenarios' in tables:
        columns = {column['name'] for column in sa.inspect(bind).get_columns('test_scenarios')}
        for name in (
            'schedule_is_active',
            'schedule_task_name',
            'schedule_webhook_url',
            'schedule_env_id',
            'schedule_cron_expression',
        ):
            if name in columns:
                op.drop_column('test_scenarios', name)
