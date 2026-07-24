"""add healing_configs.auto_mutate_assets (default false)

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-07-24 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e0f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "healing_configs" not in sa.inspect(bind).get_table_names():
        return
    columns = {column["name"] for column in sa.inspect(bind).get_columns("healing_configs")}
    if "auto_mutate_assets" not in columns:
        op.add_column(
            "healing_configs",
            sa.Column("auto_mutate_assets", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if "healing_configs" not in sa.inspect(bind).get_table_names():
        return
    columns = {column["name"] for column in sa.inspect(bind).get_columns("healing_configs")}
    if "auto_mutate_assets" in columns:
        op.drop_column("healing_configs", "auto_mutate_assets")
