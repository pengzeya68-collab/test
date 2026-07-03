"""add jmeter bench tables

Revision ID: a1b2c3d4e5f6
Revises: 9e2b3c4d5e6f
Create Date: 2026-07-04

新增 JMeter 模块的 3 张表:
- jmeter_bench_runs: 压测运行记录(支持真实 JMeter 引擎与快速预览)
- jmeter_bench_snapshots: 实时进度快照(前端轮询图表)
- jmeter_perf_baselines: 性能基线(Stage E 使用,本迁移一并创建)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "9e2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade():
    # 1. 压测运行记录
    op.create_table(
        "jmeter_bench_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("plan_name", sa.String(255), nullable=False),
        sa.Column("config_json", sa.Text),
        sa.Column("engine_type", sa.String(20), default="jmeter"),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("task_id", sa.String(64), index=True),
        sa.Column("jmx_path", sa.String(500)),
        sa.Column("jtl_path", sa.String(500)),
        sa.Column("html_report_path", sa.String(500)),
        sa.Column("summary_json", sa.Text),
        sa.Column("error_msg", sa.Text),
        sa.Column("script_hash", sa.String(64), index=True),
        sa.Column("regression", sa.Integer, default=0),
        sa.Column("started_at", sa.DateTime),
        sa.Column("finished_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
    )

    # 2. 实时进度快照
    op.create_table(
        "jmeter_bench_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "run_id",
            sa.Integer,
            sa.ForeignKey("jmeter_bench_runs.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("ts", sa.DateTime, default=sa.func.now()),
        sa.Column("percent", sa.Integer, default=0),
        sa.Column("active_threads", sa.Integer, default=0),
        sa.Column("tps", sa.Float, default=0),
        sa.Column("avg_ms", sa.Float, default=0),
        sa.Column("p95_ms", sa.Float, default=0),
        sa.Column("error_rate", sa.Float, default=0),
    )

    # 3. 性能基线(Stage E 使用,本迁移一并创建)
    op.create_table(
        "jmeter_perf_baselines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("script_hash", sa.String(64), index=True),
        sa.Column("p95_threshold_ms", sa.Integer),
        sa.Column("p99_threshold_ms", sa.Integer),
        sa.Column("tps_threshold", sa.Float),
        sa.Column("error_rate_threshold", sa.Float),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now()),
    )


def downgrade():
    op.drop_table("jmeter_perf_baselines")
    op.drop_table("jmeter_bench_snapshots")
    op.drop_table("jmeter_bench_runs")
