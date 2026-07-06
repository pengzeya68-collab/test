"""Widen jmeter script_hash columns to 128 (fallback hash is 73 chars)

Revision ID: d2e3f4a5b6c7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa


revision = "d2e3f4a5b6c7"
down_revision = "b1c2d3e4f5a6"


def upgrade():
    op.alter_column("jmeter_bench_runs", "script_hash",
                    existing_type=sa.String(64),
                    type_=sa.String(128),
                    existing_nullable=True)
    op.alter_column("jmeter_perf_baselines", "script_hash",
                    existing_type=sa.String(64),
                    type_=sa.String(128),
                    existing_nullable=True)


def downgrade():
    op.alter_column("jmeter_bench_runs", "script_hash",
                    existing_type=sa.String(128),
                    type_=sa.String(64),
                    existing_nullable=True)
    op.alter_column("jmeter_perf_baselines", "script_hash",
                    existing_type=sa.String(128),
                    type_=sa.String(64),
                    existing_nullable=True)
