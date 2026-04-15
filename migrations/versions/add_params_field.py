"""add params field to api_cases

Revision ID: add_params_field
Revises: add_extractors_field
Create Date: 2026-04-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_params_field'
down_revision = 'add_extractors_field'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('api_cases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('params', sa.JSON(), nullable=True, comment='请求参数'))


def downgrade():
    with op.batch_alter_table('api_cases', schema=None) as batch_op:
        batch_op.drop_column('params')