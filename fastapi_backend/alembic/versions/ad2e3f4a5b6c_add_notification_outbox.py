"""add durable automation notification channels and delivery outbox

Revision ID: ad2e3f4a5b6c
Revises: ac1d2e3f4a5b
Create Date: 2026-07-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ad2e3f4a5b6c"
down_revision: Union[str, Sequence[str], None] = "ac1d2e3f4a5b"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()
    if "automation_notification_channels" not in tables:
        op.create_table(
            "automation_notification_channels",
            sa.Column("id", sa.String(length=32), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("channel_type", sa.String(length=30), nullable=False),
            sa.Column("config_encrypted", sa.Text(), nullable=False),
            sa.Column("notify_on", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("user_id", "name", name="uq_automation_notification_channel_name"),
        )
        op.create_index("idx_automation_notification_channels_user_active", "automation_notification_channels", ["user_id", "is_active"])
    if "automation_notification_deliveries" not in tables:
        op.create_table(
            "automation_notification_deliveries",
            sa.Column("id", sa.String(length=32), primary_key=True),
            sa.Column("execution_id", sa.Integer(), sa.ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("channel_id", sa.String(length=32), sa.ForeignKey("automation_notification_channels.id", ondelete="SET NULL"), nullable=True),
            sa.Column("event_key", sa.String(length=180), nullable=False),
            sa.Column("channel_type", sa.String(length=30), nullable=False),
            sa.Column("payload_redacted", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("event_key", name="uq_automation_notification_delivery_event"),
        )
        op.create_index("idx_automation_notification_delivery_due", "automation_notification_deliveries", ["status", "next_attempt_at"])
        op.create_index("idx_automation_notification_delivery_execution", "automation_notification_deliveries", ["execution_id"])


def downgrade() -> None:
    tables = _tables()
    if "automation_notification_deliveries" in tables:
        op.drop_table("automation_notification_deliveries")
    if "automation_notification_channels" in tables:
        op.drop_table("automation_notification_channels")
