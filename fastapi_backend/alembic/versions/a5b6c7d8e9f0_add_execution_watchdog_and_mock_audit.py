"""add suite heartbeat and mock fault audit fields

Revision ID: a5b6c7d8e9f0
Revises: a4b5c6d7e8f9
Create Date: 2026-07-21 02:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    execution_columns = {column["name"] for column in sa.inspect(bind).get_columns("automation_executions")}
    if "heartbeat_at" not in execution_columns:
        op.add_column("automation_executions", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))

    log_columns = {column["name"] for column in sa.inspect(bind).get_columns("mock_request_logs")}
    if "fault_triggered" not in log_columns:
        op.add_column("mock_request_logs", sa.Column("fault_triggered", sa.Boolean(), nullable=False, server_default=sa.false()))
    if "fault_type" not in log_columns:
        op.add_column("mock_request_logs", sa.Column("fault_type", sa.String(length=40), nullable=True))
    if "fault_random_value" not in log_columns:
        op.add_column("mock_request_logs", sa.Column("fault_random_value", sa.Float(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    log_columns = {column["name"] for column in sa.inspect(bind).get_columns("mock_request_logs")}
    for column in ("fault_random_value", "fault_type", "fault_triggered"):
        if column in log_columns:
            op.drop_column("mock_request_logs", column)
    execution_columns = {column["name"] for column in sa.inspect(bind).get_columns("automation_executions")}
    if "heartbeat_at" in execution_columns:
        op.drop_column("automation_executions", "heartbeat_at")
