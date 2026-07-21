"""add suite schedule lease and execution policy fields

Revision ID: a7b8c9d0e1f2
Revises: a6b7c8d9e0f1
Create Date: 2026-07-21 04:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("test_suite_schedules")}
    additions = [
        ("env_id", sa.Integer(), True, None),
        ("misfire_policy", sa.String(length=20), False, "coalesce"),
        ("max_concurrent", sa.Integer(), False, "1"),
        ("last_enqueued_at", sa.DateTime(timezone=True), True, None),
        ("last_execution_id", sa.Integer(), True, None),
        ("lease_token", sa.String(length=64), True, None),
        ("lease_expires_at", sa.DateTime(timezone=True), True, None),
    ]
    for name, column_type, nullable, default in additions:
        if name not in columns:
            op.add_column(
                "test_suite_schedules",
                sa.Column(name, column_type, nullable=nullable, server_default=default),
            )


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("test_suite_schedules")}
    for name in ("lease_expires_at", "lease_token", "last_execution_id", "last_enqueued_at", "max_concurrent", "misfire_policy", "env_id"):
        if name in columns:
            op.drop_column("test_suite_schedules", name)
