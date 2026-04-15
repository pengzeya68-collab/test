"""add extractors field to api_cases

Revision ID: add_extractors_field
Revises: 
Create Date: 2026-04-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_extractors_field'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('api_cases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('extractors', sa.JSON(), nullable=True, comment='变量提取规则'))


def downgrade():
    with op.batch_alter_table('api_cases', schema=None) as batch_op:
        batch_op.drop_column('extractors')
