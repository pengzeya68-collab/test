"""migrate_remove_foreign_keys_and_add_columns

Revision ID: 5c8d9e0f1a2b
Revises: 4b7c8d9e0f1a
Create Date: 2026-05-25 13:00:00.000000

移除 submissions 和 interview_sessions 中 question_id 的外键约束，
添加 submissions.question_source 和 users.assessment_score、users.is_super_admin 列。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5c8d9e0f1a2b'
down_revision: Union[str, Sequence[str], None] = '4b7c8d9e0f1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('question_source', sa.VARCHAR(length=20), nullable=True,
                                       server_default='interview_question'))

    with op.batch_alter_table('users', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('assessment_score', sa.INTEGER(), nullable=True))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('is_super_admin', sa.BOOLEAN(), nullable=True, server_default=sa.text('0')))
        except Exception:
            pass


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_super_admin')
        batch_op.drop_column('assessment_score')

    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.drop_column('question_source')