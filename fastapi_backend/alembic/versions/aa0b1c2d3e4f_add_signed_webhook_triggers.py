"""add signed idempotent external webhook triggers

Revision ID: aa0b1c2d3e4f
Revises: a9d0e1f2a3b4
Create Date: 2026-07-21 08:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'aa0b1c2d3e4f'
down_revision = 'a9d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if 'automation_webhooks' not in tables:
        op.create_table(
            'automation_webhooks',
            sa.Column('id', sa.String(length=32), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('suite_id', sa.Integer(), sa.ForeignKey('test_suites.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('signing_secret_encrypted', sa.Text(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('allowed_clock_skew_seconds', sa.Integer(), nullable=False, server_default='300'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index('idx_automation_webhooks_user_created', 'automation_webhooks', ['user_id', 'created_at'])
        op.create_index('idx_automation_webhooks_suite', 'automation_webhooks', ['suite_id'])
        op.create_index('ix_automation_webhooks_user_id', 'automation_webhooks', ['user_id'])
    if 'automation_webhook_receipts' not in tables:
        op.create_table(
            'automation_webhook_receipts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('webhook_id', sa.String(length=32), sa.ForeignKey('automation_webhooks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('event_id', sa.String(length=128), nullable=False),
            sa.Column('request_sha256', sa.String(length=64), nullable=False),
            sa.Column('execution_id', sa.Integer(), sa.ForeignKey('automation_executions.id', ondelete='CASCADE'), nullable=False),
            sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint('webhook_id', 'event_id', name='uq_automation_webhook_event'),
        )
        op.create_index('idx_automation_webhook_receipts_execution', 'automation_webhook_receipts', ['execution_id'])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if 'automation_webhook_receipts' in tables:
        op.drop_table('automation_webhook_receipts')
    if 'automation_webhooks' in tables:
        op.drop_table('automation_webhooks')
