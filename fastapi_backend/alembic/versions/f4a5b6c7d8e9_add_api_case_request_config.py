"""Add enterprise HTTP request configuration to API cases.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
"""

from alembic import op
import sqlalchemy as sa


revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("api_cases", sa.Column("request_config", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("api_cases", "request_config")
