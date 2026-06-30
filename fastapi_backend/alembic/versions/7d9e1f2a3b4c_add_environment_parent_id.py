"""add_environment_parent_id

为 environments 表添加 parent_id 列，支持环境变量继承机制。
子环境通过 parent_id 指向父环境，变量解析时子环境覆盖父环境同名变量。
最大继承深度由应用层限制为 5 层。

Revision ID: 7d9e1f2a3b4c
Revises: f8a1c2d3e4b5
Create Date: 2026-06-26 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7d9e1f2a3b4c"
down_revision: Union[str, Sequence[str], None] = "f8a1c2d3e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 parent_id 列（自引用外键，指向 environments.id）
    op.add_column(
        "environments",
        sa.Column(
            "parent_id",
            sa.Integer(),
            nullable=True,
            comment="父环境ID(用于变量继承，最大深度5层)",
        ),
    )
    op.create_index(
        "idx_environments_parent_id",
        "environments",
        ["parent_id"],
    )
    # SQLite 不支持 ADD CONSTRAINT，这里用 try/except 兼容
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        try:
            op.create_foreign_key(
                "fk_environments_parent",
                "environments",
                "environments",
                ["parent_id"],
                ["id"],
                ondelete="SET NULL",
            )
        except Exception:
            # 约束已存在时忽略
            pass


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        try:
            op.drop_constraint("fk_environments_parent", "environments", type_="foreignkey")
        except Exception:
            pass
    op.drop_index("idx_environments_parent_id", table_name="environments")
    op.drop_column("environments", "parent_id")
