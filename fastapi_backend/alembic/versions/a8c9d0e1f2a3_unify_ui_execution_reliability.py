"""unify UI execution records, capture policy and annotation metadata

Revision ID: a8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-21 05:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()
    if "ui_runs" in tables:
        columns = _columns("ui_runs")
        additions = (
            ("automation_execution_id", sa.Column("automation_execution_id", sa.Integer(), nullable=True)),
            ("attempt", sa.Column("attempt", sa.Integer(), nullable=False, server_default="1")),
            ("last_heartbeat_at", sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True)),
            ("lease_expires_at", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True)),
        )
        for name, column in additions:
            if name not in columns:
                op.add_column("ui_runs", column)
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("ui_runs")}
        if "ix_ui_runs_automation_execution_id" not in indexes:
            op.create_index("ix_ui_runs_automation_execution_id", "ui_runs", ["automation_execution_id"], unique=True)

    if "desktop_agents" in tables and "agent_token_hash" not in _columns("desktop_agents"):
        op.add_column("desktop_agents", sa.Column("agent_token_hash", sa.String(length=64), nullable=True))

    if "ui_artifacts" in tables:
        columns = _columns("ui_artifacts")
        if "artifact_manifest_id" not in columns:
            op.add_column("ui_artifacts", sa.Column("artifact_manifest_id", sa.Integer(), nullable=True))
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("ui_artifacts")}
        if "ix_ui_artifacts_artifact_manifest_id" not in indexes:
            op.create_index("ix_ui_artifacts_artifact_manifest_id", "ui_artifacts", ["artifact_manifest_id"], unique=True)

    if "capture_sessions" in tables:
        columns = _columns("capture_sessions")
        if "capture_config" not in columns:
            op.add_column("capture_sessions", sa.Column("capture_config", sa.JSON(), nullable=True))
        if "failure_reason" not in columns:
            op.add_column("capture_sessions", sa.Column("failure_reason", sa.Text(), nullable=True))
    if "captured_exchanges" in tables and "failure_reason" not in _columns("captured_exchanges"):
        op.add_column("captured_exchanges", sa.Column("failure_reason", sa.Text(), nullable=True))

    if "artifact_annotations" not in tables:
        op.create_table(
            "artifact_annotations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("artifact_manifest_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("annotations", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("artifact_manifest_id", "user_id", name="uq_artifact_annotation_owner"),
        )
        op.create_index("idx_artifact_annotations_artifact_user", "artifact_annotations", ["artifact_manifest_id", "user_id"], unique=True)


def downgrade() -> None:
    tables = _tables()
    if "artifact_annotations" in tables:
        op.drop_table("artifact_annotations")
    if "captured_exchanges" in tables and "failure_reason" in _columns("captured_exchanges"):
        op.drop_column("captured_exchanges", "failure_reason")
    if "capture_sessions" in tables:
        for name in ("failure_reason", "capture_config"):
            if name in _columns("capture_sessions"):
                op.drop_column("capture_sessions", name)
    if "ui_artifacts" in tables:
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("ui_artifacts")}
        if "ix_ui_artifacts_artifact_manifest_id" in indexes:
            op.drop_index("ix_ui_artifacts_artifact_manifest_id", table_name="ui_artifacts")
        if "artifact_manifest_id" in _columns("ui_artifacts"):
            op.drop_column("ui_artifacts", "artifact_manifest_id")
    if "desktop_agents" in tables and "agent_token_hash" in _columns("desktop_agents"):
        op.drop_column("desktop_agents", "agent_token_hash")
    if "ui_runs" in tables:
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("ui_runs")}
        if "ix_ui_runs_automation_execution_id" in indexes:
            op.drop_index("ix_ui_runs_automation_execution_id", table_name="ui_runs")
        for name in ("lease_expires_at", "last_heartbeat_at", "attempt", "automation_execution_id"):
            if name in _columns("ui_runs"):
                op.drop_column("ui_runs", name)
