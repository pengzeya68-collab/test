"""extend jmeter_perf_baselines.name from varchar(64) to varchar(255)

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-04

修复后端日志报错:
  StringDataRightTruncationError: value too long for type character varying(64)
  parameters: (..., 'TestMaster - 健康检查_基线_2026-07-03', ...)

模型层 Column(String(255)) 与实际表结构 VARCHAR(64) 不一致,需数据库迁移对齐。
"""
from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "jmeter_perf_baselines",
        "name",
        existing_type=sa.String(length=64),
        type_=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "jmeter_perf_baselines",
        "name",
        existing_type=sa.String(length=255),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
