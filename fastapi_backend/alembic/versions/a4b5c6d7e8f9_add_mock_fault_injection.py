"""add application-layer mock fault injection

Revision ID: a4b5c6d7e8f9
Revises: a3b4c5d6e7f8
Create Date: 2026-07-21 00:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("mock_rules")}
    if "fault_type" not in columns:
        op.add_column("mock_rules", sa.Column("fault_type", sa.String(length=40), nullable=True))
    if "fault_config" not in columns:
        op.add_column("mock_rules", sa.Column("fault_config", sa.JSON(), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("mock_rules")}
    if "fault_config" in columns:
        op.drop_column("mock_rules", "fault_config")
    if "fault_type" in columns:
        op.drop_column("mock_rules", "fault_type")
