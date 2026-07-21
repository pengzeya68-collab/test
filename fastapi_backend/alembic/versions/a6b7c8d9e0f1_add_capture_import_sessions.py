"""add browser capture sessions and import jobs

Revision ID: a6b7c8d9e0f1
Revises: a5b6c7d8e9f0
Create Date: 2026-07-21 03:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, Sequence[str], None] = "a5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "capture_sessions" not in tables:
        op.create_table(
            "capture_sessions",
            sa.Column("id", sa.String(length=32), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("origin", sa.String(length=40), nullable=False, server_default="desktop_browser"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="capturing"),
            sa.Column("policy_version", sa.String(length=40), nullable=False, server_default="v1"),
            sa.Column("source_url", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_capture_sessions_user_created", "capture_sessions", ["user_id", "created_at"])
        op.create_index("ix_capture_sessions_user_id", "capture_sessions", ["user_id"])
    if "captured_exchanges" not in tables:
        op.create_table(
            "captured_exchanges",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_id", sa.String(length=32), sa.ForeignKey("capture_sessions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("method", sa.String(length=10), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("request_redacted", sa.JSON(), nullable=False),
            sa.Column("response_redacted", sa.JSON(), nullable=True),
            sa.Column("fingerprint", sa.String(length=64), nullable=False),
            sa.Column("page_url", sa.Text(), nullable=True),
            sa.Column("resource_type", sa.String(length=30), nullable=True),
            sa.Column("timing_ms", sa.Integer(), nullable=True),
            sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("session_id", "sequence", name="uq_captured_exchange_sequence"),
        )
        op.create_index("idx_captured_exchanges_session", "captured_exchanges", ["session_id"])
        op.create_index("idx_captured_exchanges_fingerprint", "captured_exchanges", ["fingerprint"])
    if "import_jobs" not in tables:
        op.create_table(
            "import_jobs",
            sa.Column("id", sa.String(length=32), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("source_type", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="previewed"),
            sa.Column("summary", sa.JSON(), nullable=True),
            sa.Column("error_summary", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_import_jobs_user_created", "import_jobs", ["user_id", "created_at"])
        op.create_index("ix_import_jobs_user_id", "import_jobs", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("import_jobs", "captured_exchanges", "capture_sessions"):
        if table in tables:
            op.drop_table(table)
