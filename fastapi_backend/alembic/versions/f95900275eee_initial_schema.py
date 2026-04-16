"""initial_schema

Revision ID: f95900275eee
Revises: 
Create Date: 2026-04-15 00:30:20.265998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f95900275eee'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('admin_users',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=80), nullable=False),
    sa.Column('password_hash', sa.VARCHAR(length=128), nullable=False),
    sa.Column('name', sa.VARCHAR(length=80), nullable=True),
    sa.Column('email', sa.VARCHAR(length=120), nullable=True),
    sa.Column('avatar', sa.VARCHAR(length=500), nullable=True),
    sa.Column('role', sa.VARCHAR(length=20), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('last_login_at', sa.DATETIME(), nullable=True),
    sa.Column('last_login_ip', sa.VARCHAR(length=50), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('auto_test_cases',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('folder_id', sa.INTEGER(), nullable=True),
    sa.Column('name', sa.VARCHAR(length=200), nullable=False),
    sa.Column('method', sa.VARCHAR(length=10), nullable=False),
    sa.Column('url', sa.VARCHAR(length=2000), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('headers', sa.TEXT(), nullable=True),
    sa.Column('body', sa.TEXT(), nullable=True),
    sa.Column('body_type', sa.VARCHAR(length=20), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.Column('extractors', sa.TEXT(), server_default=sa.text("'[]'"), nullable=True),
    sa.Column('assertions', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['folder_id'], ['auto_test_groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auto_test_plans',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('environment_id', sa.INTEGER(), nullable=True),
    sa.Column('case_ids', sa.TEXT(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.Column('data_matrix', sa.TEXT(), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('1'), nullable=True),
    sa.ForeignKeyConstraint(['environment_id'], ['interface_test_environments.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auto_test_reports',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('plan_id', sa.INTEGER(), nullable=True),
    sa.Column('plan_name', sa.VARCHAR(length=200), nullable=True),
    sa.Column('total_count', sa.INTEGER(), nullable=True),
    sa.Column('success_count', sa.INTEGER(), nullable=True),
    sa.Column('failed_count', sa.INTEGER(), nullable=True),
    sa.Column('total_time', sa.INTEGER(), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('executed_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['auto_test_plans.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auto_test_report_results',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('report_id', sa.INTEGER(), nullable=False),
    sa.Column('case_id', sa.INTEGER(), nullable=True),
    sa.Column('case_name', sa.VARCHAR(length=200), nullable=True),
    sa.Column('method', sa.VARCHAR(length=10), nullable=True),
    sa.Column('url', sa.VARCHAR(length=2000), nullable=True),
    sa.Column('status_code', sa.INTEGER(), nullable=True),
    sa.Column('success', sa.BOOLEAN(), nullable=True),
    sa.Column('time_ms', sa.INTEGER(), nullable=True),
    sa.Column('error', sa.TEXT(), nullable=True),
    sa.Column('request_headers', sa.TEXT(), nullable=True),
    sa.Column('request_body', sa.TEXT(), nullable=True),
    sa.Column('response_body', sa.TEXT(), nullable=True),
    sa.Column('response_headers', sa.TEXT(), nullable=True),
    sa.Column('executed_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['case_id'], ['auto_test_cases.id'], ),
    sa.ForeignKeyConstraint(['report_id'], ['auto_test_reports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('scheduled_tasks',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('scenario_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), nullable=True),
    sa.Column('cron_expression', sa.VARCHAR(length=50), nullable=False),
    sa.Column('env_id', sa.INTEGER(), nullable=True),
    sa.Column('webhook_url', sa.VARCHAR(length=500), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('last_run_at', sa.DATETIME(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['scenario_id'], ['test_scenarios.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auto_test_steps',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('scenario_id', sa.INTEGER(), nullable=False),
    sa.Column('api_case_id', sa.INTEGER(), nullable=False),
    sa.Column('step_order', sa.INTEGER(), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('variable_overrides', sa.TEXT(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.Column('extractors', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['api_case_id'], ['auto_test_cases.id'], ),
    sa.ForeignKeyConstraint(['scenario_id'], ['auto_test_plans.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('interview_question_collections',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('question_id', sa.INTEGER(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'question_id', name=op.f('unique_user_interview_question'))
    )
    op.create_table('audit_logs',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.Column('admin_id', sa.INTEGER(), nullable=True),
    sa.Column('action', sa.VARCHAR(length=200), nullable=False),
    sa.Column('action_type', sa.VARCHAR(length=50), nullable=False),
    sa.Column('ip_address', sa.VARCHAR(length=50), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['admin_users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('interview_question_records',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('session_id', sa.INTEGER(), nullable=False),
    sa.Column('question_id', sa.INTEGER(), nullable=False),
    sa.Column('user_answer', sa.TEXT(), nullable=True),
    sa.Column('ai_feedback', sa.TEXT(), nullable=True),
    sa.Column('score', sa.INTEGER(), nullable=True),
    sa.Column('is_answered', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('test_scenarios',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('environment_id', sa.INTEGER(), nullable=True),
    sa.Column('case_ids', sa.TEXT(), nullable=False),
    sa.Column('data_matrix', sa.TEXT(), nullable=True),
    sa.Column('cron_expression', sa.VARCHAR(length=50), nullable=True),
    sa.Column('webhook_url', sa.VARCHAR(length=500), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.Column('webhook_token', sa.VARCHAR(length=64), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_test_scenarios_webhook_token'), ['webhook_token'], unique=1)

    with op.batch_alter_table('auto_test_groups', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_auto_test_groups_id'), ['id'], unique=False)
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_comments_id'), ['id'], unique=False)
    with op.batch_alter_table('exam_answers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_exam_answers_id'), ['id'], unique=False)
    with op.batch_alter_table('exam_attempts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_exam_attempts_id'), ['id'], unique=False)
    with op.batch_alter_table('exam_questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('test_cases', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_exam_questions_id'), ['id'], unique=False)
    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_exams_id'), ['id'], unique=False)
    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_exercises_id'), ['id'], unique=False)
    with op.batch_alter_table('favorites', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_favorites_id'), ['id'], unique=False)
    with op.batch_alter_table('interface_test_cases', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interface_test_cases_id'), ['id'], unique=False)
    with op.batch_alter_table('interface_test_environments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interface_test_environments_id'), ['id'], unique=False)
    with op.batch_alter_table('interface_test_folders', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interface_test_folders_id'), ['id'], unique=False)
    with op.batch_alter_table('interface_test_plans', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interface_test_plans_id'), ['id'], unique=False)
    with op.batch_alter_table('interface_test_report_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interface_test_report_results_id'), ['id'], unique=False)
    with op.batch_alter_table('interface_test_reports', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interface_test_reports_id'), ['id'], unique=False)
    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_questions_id'), ['id'], unique=False)
        batch_op.create_unique_constraint(None, ['slug'])
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_sessions_id'), ['id'], unique=False)
    with op.batch_alter_table('interview_test_cases', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_test_cases_id'), ['id'], unique=False)
    with op.batch_alter_table('learning_paths', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_paths_id'), ['id'], unique=False)
    with op.batch_alter_table('likes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_likes_id'), ['id'], unique=False)
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_posts_id'), ['id'], unique=False)
    with op.batch_alter_table('progress', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_progress_id'), ['id'], unique=False)
    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_submissions_id'), ['id'], unique=False)
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_id'), ['id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_id'))
    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_submissions_id'))
    with op.batch_alter_table('progress', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_progress_id'))
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_posts_id'))
    with op.batch_alter_table('likes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_likes_id'))
    with op.batch_alter_table('learning_paths', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_paths_id'))
    with op.batch_alter_table('interview_test_cases', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_test_cases_id'))
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_sessions_id'))
    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_index(batch_op.f('ix_interview_questions_id'))
    with op.batch_alter_table('interface_test_reports', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interface_test_reports_id'))
    with op.batch_alter_table('interface_test_report_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interface_test_report_results_id'))
    with op.batch_alter_table('interface_test_plans', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interface_test_plans_id'))
    with op.batch_alter_table('interface_test_folders', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interface_test_folders_id'))
    with op.batch_alter_table('interface_test_environments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interface_test_environments_id'))
    with op.batch_alter_table('interface_test_cases', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interface_test_cases_id'))
    with op.batch_alter_table('favorites', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_favorites_id'))
    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exercises_id'))
    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exams_id'))
    with op.batch_alter_table('exam_questions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exam_questions_id'))
        batch_op.drop_column('test_cases')
    with op.batch_alter_table('exam_attempts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exam_attempts_id'))
    with op.batch_alter_table('exam_answers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exam_answers_id'))
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_comments_id'))
    with op.batch_alter_table('auto_test_groups', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_auto_test_groups_id'))
    with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_test_scenarios_webhook_token'))
    op.drop_table('interview_question_records')
    op.drop_table('audit_logs')
    op.drop_table('interview_question_collections')
    op.drop_table('auto_test_steps')
    op.drop_table('test_scenarios')
    op.drop_table('scheduled_tasks')
    op.drop_table('auto_test_report_results')
    op.drop_table('auto_test_reports')
    op.drop_table('auto_test_cases')
    op.drop_table('auto_test_plans')
    op.drop_table('admin_users')
