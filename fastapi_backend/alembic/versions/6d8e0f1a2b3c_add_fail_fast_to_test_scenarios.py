"""add fail_fast to test_scenarios

Revision ID: 6d8e0f1a2b3c
Revises: 5c8d9e0f1a2b
Create Date: 2026-05-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6d8e0f1a2b3c'
down_revision: Union[str, Sequence[str], None] = '5c8d9e0f1a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('fail_fast', sa.Boolean(), nullable=True, server_default='0'))
        except Exception:
            pass


def downgrade() -> None:
    with op.batch_alter_table('test_scenarios', schema=None) as batch_op:
        try:
            batch_op.drop_column('fail_fast')
        except Exception:
            pass
