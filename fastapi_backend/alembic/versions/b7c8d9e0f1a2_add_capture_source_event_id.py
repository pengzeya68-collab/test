"""add idempotent source event identifiers to captured exchanges

Revision ID: b7c8d9e0f1a2
Revises: ad2e3f4a5b6c
Create Date: 2026-07-24 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "ad2e3f4a5b6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("captured_exchanges")}
    if "source_event_id" not in columns:
        op.add_column("captured_exchanges", sa.Column("source_event_id", sa.String(length=64), nullable=True))
        op.create_index("ix_captured_exchanges_source_event_id", "captured_exchanges", ["source_event_id"])


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("captured_exchanges")}
    if "source_event_id" in columns:
        op.drop_index("ix_captured_exchanges_source_event_id", table_name="captured_exchanges")
        op.drop_column("captured_exchanges", "source_event_id")
