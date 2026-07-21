"""add database-backed suites and execution foundation

Revision ID: a2b3c4d5e6f7
Revises: f4a5b6c7d8e9
Create Date: 2026-07-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    tables = _table_names()
    if "test_suites" not in tables:
        op.create_table(
            "test_suites",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("env_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("kind", sa.String(length=20), nullable=False, server_default="scenario"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("legacy_key", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        tables.add("test_suites")
    else:
        columns = _column_names("test_suites")
        if "kind" not in columns:
            op.add_column("test_suites", sa.Column("kind", sa.String(length=20), nullable=False, server_default="scenario"))
        if "is_active" not in columns:
            op.add_column("test_suites", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
        if "legacy_key" not in columns:
            op.add_column("test_suites", sa.Column("legacy_key", sa.String(length=100), nullable=True))

    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("test_suites")}
    if "ix_test_suites_legacy_key" not in indexes:
        op.create_index("ix_test_suites_legacy_key", "test_suites", ["legacy_key"], unique=True)

    tables = _table_names()
    if "test_suite_scenarios" not in tables:
        op.create_table(
            "test_suite_scenarios",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("suite_id", sa.Integer(), sa.ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False),
            sa.Column("scenario_id", sa.Integer(), sa.ForeignKey("test_scenarios.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("suite_id", "scenario_id", name="uq_suite_scenario"),
        )
        op.create_index("idx_suite_scenarios_suite_id", "test_suite_scenarios", ["suite_id"])

    if "test_suite_schedules" not in tables:
        op.create_table(
            "test_suite_schedules",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("suite_id", sa.Integer(), sa.ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False),
            sa.Column("cron_expression", sa.String(length=200), nullable=False),
            sa.Column("timezone_name", sa.String(length=100), nullable=False, server_default="Asia/Shanghai"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("notification_config", sa.JSON(), nullable=True),
            sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("suite_id", name="uq_suite_schedule"),
        )

    if "automation_executions" not in tables:
        op.create_table(
            "automation_executions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("public_id", sa.String(length=32), nullable=False, unique=True),
            sa.Column("execution_type", sa.String(length=30), nullable=False, server_default="suite"),
            sa.Column("target_type", sa.String(length=30), nullable=False, server_default="suite"),
            sa.Column("target_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("env_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
            sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("runner_id", sa.String(length=200), nullable=True),
            sa.Column("error_code", sa.String(length=100), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("result_summary", sa.JSON(), nullable=True),
            sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("idempotency_key", name="uq_automation_execution_idempotency"),
        )
        op.create_index("idx_automation_execution_target", "automation_executions", ["target_type", "target_id"])
        op.create_index("idx_automation_execution_user_created", "automation_executions", ["user_id", "created_at"])

    if "automation_execution_items" not in tables:
        op.create_table(
            "automation_execution_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("execution_id", sa.Integer(), sa.ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("target_type", sa.String(length=30), nullable=False),
            sa.Column("target_id", sa.Integer(), nullable=False),
            sa.Column("target_name", sa.String(length=300), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
            sa.Column("result_summary", sa.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("execution_id", "sequence", name="uq_execution_item_sequence"),
        )
        op.create_index("idx_execution_items_execution_id", "automation_execution_items", ["execution_id"])

    if "execution_events" not in tables:
        op.create_table(
            "execution_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("execution_id", sa.Integer(), sa.ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("level", sa.String(length=20), nullable=False, server_default="info"),
            sa.Column("event_type", sa.String(length=80), nullable=False),
            sa.Column("payload_redacted", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("execution_id", "sequence", name="uq_execution_event_sequence"),
        )
        op.create_index("idx_execution_events_execution_sequence", "execution_events", ["execution_id", "sequence"])

    if "artifact_manifests" not in tables:
        op.create_table(
            "artifact_manifests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("execution_id", sa.Integer(), sa.ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("kind", sa.String(length=40), nullable=False),
            sa.Column("filename", sa.String(length=500), nullable=False),
            sa.Column("content_type", sa.String(length=200), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("storage_key", sa.String(length=1000), nullable=False, unique=True),
            sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("execution_id", "sha256", name="uq_execution_artifact_hash"),
        )
        op.create_index("idx_artifacts_execution_id", "artifact_manifests", ["execution_id"])


def downgrade() -> None:
    for table_name in (
        "artifact_manifests",
        "execution_events",
        "automation_execution_items",
        "automation_executions",
        "test_suite_schedules",
        "test_suite_scenarios",
    ):
        if table_name in _table_names():
            op.drop_table(table_name)

    if "test_suites" in _table_names():
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("test_suites")}
        if "ix_test_suites_legacy_key" in indexes:
            op.drop_index("ix_test_suites_legacy_key", table_name="test_suites")
        columns = _column_names("test_suites")
        for column in ("legacy_key", "is_active", "kind"):
            if column in columns:
                op.drop_column("test_suites", column)
