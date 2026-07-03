"""add assert_templates table

新增 autotest_assert_templates 表，支持断言模板库持久化（内置 + 用户自定义）。

Revision ID: 9e2b3c4d5e6f
Revises: 7d9e1f2a3b4c
Create Date: 2026-07-03 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9e2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "7d9e1f2a3b4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - 创建断言模板表"""
    op.create_table(
        "autotest_assert_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False, comment="模板名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="模板描述"),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="自定义", comment="分类"),
        sa.Column("rules", sa.JSON(), nullable=False, server_default="[]", comment="断言规则数组"),
        sa.Column("code_snippet", sa.Text(), nullable=True, comment="代码示例"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.text("false"), comment="是否内置模板"),
        sa.Column("user_id", sa.Integer(), nullable=True, comment="创建者用户ID(跨库引用,非FK,NULL=系统内置)"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_assert_tpl_user_id", "autotest_assert_templates", ["user_id"])
    op.create_index("idx_assert_tpl_category", "autotest_assert_templates", ["category"])


def downgrade() -> None:
    """Downgrade schema - 删除断言模板表"""
    op.drop_index("idx_assert_tpl_category", table_name="autotest_assert_templates")
    op.drop_index("idx_assert_tpl_user_id", table_name="autotest_assert_templates")
    op.drop_table("autotest_assert_templates")
