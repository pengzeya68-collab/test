"""add_rbac_tables

Revision ID: 3a62ae184c47
Revises: f95900275eee
Create Date: 2026-05-20 23:55:06.168992

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a62ae184c47"
down_revision: Union[str, Sequence[str], None] = "f95900275eee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - 创建 RBAC 相关表"""
    # 1. 创建 roles 表
    op.create_table(
        "roles",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("name", sa.VARCHAR(length=50), nullable=False),
        sa.Column("display_name", sa.VARCHAR(length=100), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("is_system", sa.BOOLEAN(), nullable=True, default=False),
        sa.Column(
            "created_at",
            sa.DATETIME(),
            nullable=True,
            default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DATETIME(),
            nullable=True,
            default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 2. 创建 permissions 表
    op.create_table(
        "permissions",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("code", sa.VARCHAR(length=100), nullable=False),
        sa.Column("name", sa.VARCHAR(length=100), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("module", sa.VARCHAR(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DATETIME(),
            nullable=True,
            default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # 3. 创建 role_permissions 表
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("role_id", sa.INTEGER(), nullable=False),
        sa.Column("permission_id", sa.INTEGER(), nullable=False),
        sa.Column(
            "created_at",
            sa.DATETIME(),
            nullable=True,
            default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.Index("idx_rbac_role_perm", "role_id", "permission_id", unique=True),
    )

    # 4. 为 users 表添加 role_id 字段
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("role_id", sa.INTEGER(), nullable=True))
        batch_op.create_index("idx_users_role_id", ["role_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_users_role_id", "roles", ["role_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    """Downgrade schema - 回滚 RBAC 相关表"""
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_role_id", type_="foreignkey")
        batch_op.drop_index("idx_users_role_id")
        batch_op.drop_column("role_id")

    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
