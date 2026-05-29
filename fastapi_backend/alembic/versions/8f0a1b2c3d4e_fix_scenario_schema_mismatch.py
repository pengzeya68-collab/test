"""fix_scenario_schema_mismatch

Revision ID: 8f0a1b2c3d4e
Revises: 7e9f0a1b2c3d
Create Date: 2026-05-30

Fix column name mismatch in test_scenarios table between old schema and new model.
Old columns: cron_expression, webhook_url, case_ids, data_matrix, environment_id, user_id
New columns: schedule_cron_expression, schedule_webhook_url, schedule_env_id, 
             schedule_task_name, schedule_is_active, project_id, fail_fast, webhook_token
"""
from alembic import op
import sqlalchemy as sa

revision = "8f0a1b2c3d4e"
down_revision = "7e9f0a1b2c3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name'] for col in inspector.get_columns('test_scenarios')}

    old_columns_present = columns & {'cron_expression', 'webhook_url', 'case_ids', 'data_matrix', 'environment_id', 'user_id'}

    if old_columns_present:
        if 'user_id' in columns:
            try:
                op.execute("ALTER TABLE test_scenarios DROP CONSTRAINT IF EXISTS test_scenarios_user_id_fkey")
            except Exception:
                pass

        if 'cron_expression' in columns and 'schedule_cron_expression' not in columns:
            with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
                try:
                    batch_op.alter_column('cron_expression', new_column_name='schedule_cron_expression')
                except Exception:
                    pass

        if 'webhook_url' in columns and 'schedule_webhook_url' not in columns:
            with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
                try:
                    batch_op.alter_column('webhook_url', new_column_name='schedule_webhook_url')
                except Exception:
                    pass

        if 'environment_id' in columns and 'schedule_env_id' not in columns:
            with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
                try:
                    batch_op.alter_column('environment_id', new_column_name='schedule_env_id')
                except Exception:
                    pass

        if 'case_ids' in columns:
            with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
                try:
                    batch_op.drop_column('case_ids')
                except Exception:
                    pass

        if 'data_matrix' in columns:
            with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
                try:
                    batch_op.drop_column('data_matrix')
                except Exception:
                    pass

        if 'user_id' in columns:
            with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
                try:
                    batch_op.drop_column('user_id')
                except Exception:
                    pass

    with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('schedule_task_name', sa.String(200), nullable=True))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('schedule_is_active', sa.Boolean(), nullable=True, server_default='1'))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('fail_fast', sa.Boolean(), nullable=True, server_default='0'))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('webhook_token', sa.String(64), nullable=True))
        except Exception:
            pass


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name'] for col in inspector.get_columns('test_scenarios')}

    with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
        if 'schedule_cron_expression' in columns:
            try:
                batch_op.alter_column('schedule_cron_expression', new_column_name='cron_expression')
            except Exception:
                pass
        if 'schedule_webhook_url' in columns:
            try:
                batch_op.alter_column('schedule_webhook_url', new_column_name='webhook_url')
            except Exception:
                pass
        if 'schedule_env_id' in columns:
            try:
                batch_op.alter_column('schedule_env_id', new_column_name='environment_id')
            except Exception:
                pass
        try:
            batch_op.drop_column('schedule_task_name')
        except Exception:
            pass
        try:
            batch_op.drop_column('schedule_is_active')
        except Exception:
            pass
        try:
            batch_op.drop_column('project_id')
        except Exception:
            pass
        try:
            batch_op.drop_column('fail_fast')
        except Exception:
            pass
        try:
            batch_op.drop_column('webhook_token')
        except Exception:
            pass
