"""Scope remaining Phase A assets to WorkspaceProject.

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-07-24 21:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def _tables(bind) -> set[str]:
    return set(sa.inspect(bind).get_table_names())


def _columns(bind, table: str) -> set[str]:
    if table not in _tables(bind):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table)}


def _add_column(bind, table: str, column: sa.Column) -> None:
    if table in _tables(bind) and column.name not in _columns(bind, table):
        op.add_column(table, column)


def _create_index(bind, name: str, table: str, columns: list[str]) -> None:
    if table not in _tables(bind):
        return
    if name in {index["name"] for index in sa.inspect(bind).get_indexes(table)}:
        return
    op.create_index(name, table, columns)


def _backfill_personal_project(bind, table: str, owner_column: str = "user_id") -> None:
    if (
        table not in _tables(bind)
        or "project_id" not in _columns(bind, table)
        or owner_column not in _columns(bind, table)
        or "workspace_projects" not in _tables(bind)
    ):
        return
    bind.execute(
        sa.text(
            f"UPDATE {table} SET project_id = ("
            "SELECT id FROM workspace_projects "
            f"WHERE owner_id = {table}.{owner_column} AND is_personal = TRUE LIMIT 1"
            ") WHERE project_id IS NULL"
        )
    )


def upgrade() -> None:
    bind = op.get_bind()
    for table, owner_column in (
        ("desktop_agents", "owner_id"),
        ("capture_sessions", "user_id"),
        ("import_jobs", "user_id"),
        ("automation_notification_channels", "user_id"),
        ("automation_notification_deliveries", "user_id"),
    ):
        _add_column(bind, table, sa.Column("project_id", sa.Integer(), nullable=True))
        _backfill_personal_project(bind, table, owner_column)

    _create_index(bind, "idx_desktop_agents_project_id", "desktop_agents", ["project_id"])
    _create_index(bind, "idx_capture_sessions_project_created", "capture_sessions", ["project_id", "created_at"])
    _create_index(bind, "idx_automation_notification_channels_project_active", "automation_notification_channels", ["project_id", "is_active"])
    _create_index(bind, "idx_automation_notification_delivery_project", "automation_notification_deliveries", ["project_id", "created_at"])

    # A channel name is project-local.  Keep a named constraint so this also
    # works on SQLite batch migrations and does not rely on application races.
    table = "automation_notification_channels"
    if table in _tables(bind):
        constraints = {item.get("name") for item in sa.inspect(bind).get_unique_constraints(table)}
        with op.batch_alter_table(table) as batch:
            if "uq_automation_notification_channel_name" in constraints:
                batch.drop_constraint("uq_automation_notification_channel_name", type_="unique")
            if "uq_automation_notification_channel_project_name" not in constraints:
                batch.create_unique_constraint(
                    "uq_automation_notification_channel_project_name", ["project_id", "name"]
                )


def downgrade() -> None:
    # Project ownership is intentionally retained on downgrade.  Removing it
    # would make a rollback silently merge tenant data again.
    pass
