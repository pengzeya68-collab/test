"""add jmeter_bench_samples table

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-07-04

Stage F.4 修复 BUG 2 引入:之前 sampler 详情被丢弃,前端"采样器列表"全 200 + 空响应。
现在把每条 JTL 采样落库,前端通过 /api/auto-test/jmeter/runs/{id}/samples 查询。
"""
from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jmeter_bench_samples",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "run_id",
            sa.Integer,
            sa.ForeignKey("jmeter_bench_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("label", sa.String(500)),
        sa.Column("method", sa.String(20)),
        sa.Column("url", sa.Text),
        sa.Column("response_code", sa.String(20)),
        sa.Column("response_message", sa.String(255)),
        sa.Column("elapsed_ms", sa.Integer, default=0),
        sa.Column("latency_ms", sa.Integer, default=0),
        sa.Column("bytes_received", sa.Integer, default=0),
        sa.Column("bytes_sent", sa.Integer, default=0),
        sa.Column("success", sa.Boolean, default=True),
        sa.Column("failure_message", sa.Text),
        sa.Column("request_data", sa.Text),
        sa.Column("response_data", sa.Text),
        sa.Column("request_headers", sa.Text),
        sa.Column("response_headers", sa.Text),
        sa.Column("thread_name", sa.String(255)),
        sa.Column("ts", sa.DateTime, default=sa.func.now(), index=True),
    )


def downgrade():
    op.drop_table("jmeter_bench_samples")
