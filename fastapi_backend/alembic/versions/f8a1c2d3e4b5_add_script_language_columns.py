"""add script_language columns

为 api_cases / scenario_steps 增加 pre_script_language、post_script_language 列，
支持 Python 后置脚本（对标 Apifox）。默认值 'javascript'，向后兼容。

Revision ID: f8a1c2d3e4b5
Revises: 5c8d9e0f1a2b
Create Date: 2026-06-26 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8a1c2d3e4b5"
down_revision: Union[str, Sequence[str], None] = "5c8d9e0f1a2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - 新增脚本语言列"""
    # api_cases：用例前后置脚本语言
    op.add_column(
        "api_cases",
        sa.Column(
            "pre_script_language",
            sa.String(length=20),
            nullable=False,
            server_default="javascript",
            comment="前置脚本语言: javascript/python",
        ),
    )
    op.add_column(
        "api_cases",
        sa.Column(
            "post_script_language",
            sa.String(length=20),
            nullable=False,
            server_default="javascript",
            comment="后置脚本语言: javascript/python",
        ),
    )
    # scenario_steps：场景步骤前后置脚本语言
    op.add_column(
        "scenario_steps",
        sa.Column(
            "pre_script_language",
            sa.String(length=20),
            nullable=False,
            server_default="javascript",
            comment="前置脚本语言: javascript/python",
        ),
    )
    op.add_column(
        "scenario_steps",
        sa.Column(
            "post_script_language",
            sa.String(length=20),
            nullable=False,
            server_default="javascript",
            comment="后置脚本语言: javascript/python",
        ),
    )


def downgrade() -> None:
    """Downgrade schema - 移除脚本语言列"""
    op.drop_column("scenario_steps", "post_script_language")
    op.drop_column("scenario_steps", "pre_script_language")
    op.drop_column("api_cases", "post_script_language")
    op.drop_column("api_cases", "pre_script_language")
