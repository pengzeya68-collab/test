"""Add indexes, constraints, fail_fast, created_at, and fix column types

Revision ID: 7e9f0a1b2c3d
Revises: 6d8e0f1a2b3c
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "7e9f0a1b2c3d"
down_revision = "6d8e0f1a2b3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("api_cases", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("test_scenarios", sa.Column("fail_fast", sa.Boolean(), nullable=True, server_default=sa.text("false")))

    op.alter_column("performance_execution_records", "error_rate", existing_type=sa.Integer(), type_=sa.Float(), existing_nullable=True)

    op.create_index("idx_api_cases_group_id", "api_cases", ["group_id"])
    op.create_index("idx_test_history_case_id", "test_history", ["case_id"])
    op.create_index("idx_test_history_created_at", "test_history", ["created_at"])
    op.create_index("idx_scenario_steps_scenario_id", "scenario_steps", ["scenario_id"])
    op.create_index("idx_scenario_steps_api_case_id", "scenario_steps", ["api_case_id"])
    op.create_index("idx_scenario_exec_records_scenario_id", "scenario_execution_records", ["scenario_id"])
    op.create_index("idx_scenario_exec_records_created_at", "scenario_execution_records", ["created_at"])
    op.create_index("idx_perf_metrics_execution_id", "performance_metrics", ["execution_id"])
    op.create_index("idx_api_groups_parent_id", "api_groups", ["parent_id"])
    op.create_index("idx_environments_is_default", "environments", ["is_default"])
    op.create_index("idx_template_fields_template_id", "test_data_template_fields", ["template_id"])

    op.create_unique_constraint("uq_environments_env_name", "environments", ["env_name"])
    op.create_unique_constraint("uq_scenario_step_order", "scenario_steps", ["scenario_id", "step_order"])

    op.alter_column("scenario_steps", "api_case_id", existing_type=sa.Integer(), nullable=True)

    op.execute("""
        ALTER TABLE api_cases DROP CONSTRAINT IF EXISTS api_cases_group_id_fkey;
        ALTER TABLE api_cases ADD CONSTRAINT api_cases_group_id_fkey
            FOREIGN KEY (group_id) REFERENCES api_groups(id) ON DELETE SET NULL;

        ALTER TABLE api_groups DROP CONSTRAINT IF EXISTS api_groups_parent_id_fkey;
        ALTER TABLE api_groups ADD CONSTRAINT api_groups_parent_id_fkey
            FOREIGN KEY (parent_id) REFERENCES api_groups(id) ON DELETE SET NULL;

        ALTER TABLE test_history DROP CONSTRAINT IF EXISTS test_history_case_id_fkey;
        ALTER TABLE test_history ADD CONSTRAINT test_history_case_id_fkey
            FOREIGN KEY (case_id) REFERENCES api_cases(id) ON DELETE CASCADE;

        ALTER TABLE scenario_steps DROP CONSTRAINT IF EXISTS scenario_steps_scenario_id_fkey;
        ALTER TABLE scenario_steps ADD CONSTRAINT scenario_steps_scenario_id_fkey
            FOREIGN KEY (scenario_id) REFERENCES test_scenarios(id) ON DELETE CASCADE;

        ALTER TABLE scenario_steps DROP CONSTRAINT IF EXISTS scenario_steps_api_case_id_fkey;
        ALTER TABLE scenario_steps ADD CONSTRAINT scenario_steps_api_case_id_fkey
            FOREIGN KEY (api_case_id) REFERENCES api_cases(id) ON DELETE SET NULL;

        ALTER TABLE test_datasets DROP CONSTRAINT IF EXISTS test_datasets_scenario_id_fkey;
        ALTER TABLE test_datasets ADD CONSTRAINT test_datasets_scenario_id_fkey
            FOREIGN KEY (scenario_id) REFERENCES test_scenarios(id) ON DELETE CASCADE;

        ALTER TABLE scenario_execution_records DROP CONSTRAINT IF EXISTS scenario_execution_records_scenario_id_fkey;
        ALTER TABLE scenario_execution_records ADD CONSTRAINT scenario_execution_records_scenario_id_fkey
            FOREIGN KEY (scenario_id) REFERENCES test_scenarios(id) ON DELETE CASCADE;

        ALTER TABLE performance_scenario_steps DROP CONSTRAINT IF EXISTS performance_scenario_steps_scenario_id_fkey;
        ALTER TABLE performance_scenario_steps ADD CONSTRAINT performance_scenario_steps_scenario_id_fkey
            FOREIGN KEY (scenario_id) REFERENCES performance_scenarios(id) ON DELETE CASCADE;

        ALTER TABLE performance_execution_records DROP CONSTRAINT IF EXISTS performance_execution_records_scenario_id_fkey;
        ALTER TABLE performance_execution_records ADD CONSTRAINT performance_execution_records_scenario_id_fkey
            FOREIGN KEY (scenario_id) REFERENCES performance_scenarios(id) ON DELETE CASCADE;

        ALTER TABLE performance_metrics DROP CONSTRAINT IF EXISTS performance_metrics_execution_id_fkey;
        ALTER TABLE performance_metrics ADD CONSTRAINT performance_metrics_execution_id_fkey
            FOREIGN KEY (execution_id) REFERENCES performance_execution_records(id) ON DELETE CASCADE;

        ALTER TABLE test_data_template_fields DROP CONSTRAINT IF EXISTS test_data_template_fields_template_id_fkey;
        ALTER TABLE test_data_template_fields ADD CONSTRAINT test_data_template_fields_template_id_fkey
            FOREIGN KEY (template_id) REFERENCES test_data_templates(id) ON DELETE CASCADE;
    """)


def downgrade() -> None:
    op.drop_column("api_cases", "created_at")
    op.drop_column("test_scenarios", "fail_fast")
    op.alter_column("performance_execution_records", "error_rate", existing_type=sa.Float(), type_=sa.Integer(), existing_nullable=True)

    op.drop_index("idx_api_cases_group_id", "api_cases")
    op.drop_index("idx_test_history_case_id", "test_history")
    op.drop_index("idx_test_history_created_at", "test_history")
    op.drop_index("idx_scenario_steps_scenario_id", "scenario_steps")
    op.drop_index("idx_scenario_steps_api_case_id", "scenario_steps")
    op.drop_index("idx_scenario_exec_records_scenario_id", "scenario_execution_records")
    op.drop_index("idx_scenario_exec_records_created_at", "scenario_execution_records")
    op.drop_index("idx_perf_metrics_execution_id", "performance_metrics")
    op.drop_index("idx_api_groups_parent_id", "api_groups")
    op.drop_index("idx_environments_is_default", "environments")
    op.drop_index("idx_template_fields_template_id", "test_data_template_fields")

    op.drop_constraint("uq_environments_env_name", "environments")
    op.drop_constraint("uq_scenario_step_order", "scenario_steps")

    op.alter_column("scenario_steps", "api_case_id", existing_type=sa.Integer(), nullable=False)
