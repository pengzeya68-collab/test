"""add_token_blacklist

Revision ID: 4b7c8d9e0f1a
Revises: 3a62ae184c47
Create Date: 2026-05-25 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b7c8d9e0f1a"
down_revision: Union[str, Sequence[str], None] = "3a62ae184c47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("token_hash", sa.VARCHAR(length=64), nullable=False),
        sa.Column(
            "token_type", sa.VARCHAR(length=20), nullable=True, server_default="access"
        ),
        sa.Column("user_id", sa.INTEGER(), nullable=True),
        sa.Column("expires_at", sa.DATETIME(), nullable=False),
        sa.Column("blacklisted_at", sa.DATETIME(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_token_blacklist_hash", "token_blacklist", ["token_hash"])
    op.create_index("idx_token_blacklist_expires", "token_blacklist", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_token_blacklist_expires", table_name="token_blacklist")
    op.drop_index("idx_token_blacklist_hash", table_name="token_blacklist")
    op.drop_table("token_blacklist")
