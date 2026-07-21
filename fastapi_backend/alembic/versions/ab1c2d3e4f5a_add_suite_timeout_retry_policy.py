"""add timeout and retry policy to persistent suite schedules

Revision ID: ab1c2d3e4f5a
Revises: aa0b1c2d3e4f
Create Date: 2026-07-21 21:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "ab1c2d3e4f5a"
down_revision = "aa0b1c2d3e4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {
        column["name"] for column in sa.inspect(op.get_bind()).get_columns("test_suite_schedules")
    }
    if "execution_timeout_seconds" not in columns:
        op.add_column(
            "test_suite_schedules",
            sa.Column("execution_timeout_seconds", sa.Integer(), nullable=False, server_default="1800"),
        )
    if "max_retries" not in columns:
        op.add_column(
            "test_suite_schedules",
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    columns = {
        column["name"] for column in sa.inspect(op.get_bind()).get_columns("test_suite_schedules")
    }
    if "max_retries" in columns:
        op.drop_column("test_suite_schedules", "max_retries")
    if "execution_timeout_seconds" in columns:
        op.drop_column("test_suite_schedules", "execution_timeout_seconds")
