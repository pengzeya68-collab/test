"""add resumable artifact upload sessions

Revision ID: a3b4c5d6e7f8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-21 00:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "artifact_upload_sessions" in tables:
        return
    op.create_table(
        "artifact_upload_sessions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("execution_id", sa.Integer(), sa.ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=200), nullable=True),
        sa.Column("expected_size_bytes", sa.Integer(), nullable=False),
        sa.Column("expected_sha256", sa.String(length=64), nullable=False),
        sa.Column("received_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("temp_storage_key", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_artifact_upload_execution", "artifact_upload_sessions", ["execution_id"])
    op.create_index("ix_artifact_upload_sessions_user_id", "artifact_upload_sessions", ["user_id"])


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "artifact_upload_sessions" in tables:
        op.drop_table("artifact_upload_sessions")
