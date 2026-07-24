"""Phase A: workspace projects + asset project_id backfill

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-07-24 20:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e0f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def _tables(bind) -> set[str]:
    return set(sa.inspect(bind).get_table_names())


def _columns(bind, table: str) -> set[str]:
    if table not in _tables(bind):
        return set()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def _add_column_if_missing(bind, table: str, column: sa.Column) -> None:
    if table not in _tables(bind):
        return
    if column.name in _columns(bind, table):
        return
    op.add_column(table, column)


def _create_index_safe(name: str, table: str, cols: list[str]) -> None:
    bind = op.get_bind()
    if table not in _tables(bind):
        return
    existing = {i["name"] for i in sa.inspect(bind).get_indexes(table)}
    if name in existing:
        return
    try:
        op.create_index(name, table, cols)
    except Exception:
        pass


def upgrade() -> None:
    bind = op.get_bind()
    tables = _tables(bind)

    if "workspace_projects" not in tables:
        op.create_table(
            "workspace_projects",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("key", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("is_personal", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("key", name="uq_workspace_projects_key"),
        )
        op.create_index("idx_workspace_projects_owner_id", "workspace_projects", ["owner_id"])

    if "workspace_project_members" not in _tables(bind):
        op.create_table(
            "workspace_project_members",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "project_id",
                sa.Integer(),
                sa.ForeignKey("workspace_projects.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("project_id", "user_id", name="uq_workspace_project_member"),
        )
        op.create_index("idx_workspace_project_members_user", "workspace_project_members", ["user_id"])
        op.create_index(
            "idx_workspace_project_members_project", "workspace_project_members", ["project_id"]
        )

    # --- nullable project_id / workspace_project_id on core assets ---
    asset_tables_project_id = [
        "api_cases",
        "api_groups",
        "environments",
        "global_variables",
        "test_suites",
        "automation_executions",
        "ui_case_groups",
    ]
    for table in asset_tables_project_id:
        _add_column_if_missing(bind, table, sa.Column("project_id", sa.Integer(), nullable=True))
        _create_index_safe(f"idx_{table}_workspace_project_id", table, ["project_id"])

    # Learning scenario already has project_id (ProjectSpace) — use workspace_project_id
    _add_column_if_missing(
        bind, "test_scenarios", sa.Column("workspace_project_id", sa.Integer(), nullable=True)
    )
    _create_index_safe("idx_test_scenarios_workspace_project_id", "test_scenarios", ["workspace_project_id"])

    # UI / AE notify gate
    _add_column_if_missing(
        bind, "automation_executions", sa.Column("notify_on_terminal", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    _add_column_if_missing(
        bind, "automation_executions", sa.Column("parent_execution_id", sa.Integer(), nullable=True)
    )
    _add_column_if_missing(bind, "ui_runs", sa.Column("parent_run_id", sa.Integer(), nullable=True))
    _create_index_safe("idx_ui_runs_parent_run_id", "ui_runs", ["parent_run_id"])

    # --- personal project backfill from distinct user_ids ---
    user_ids: set[int] = set()
    for table, col in [
        ("api_cases", "user_id"),
        ("api_groups", "user_id"),
        ("environments", "user_id"),
        ("global_variables", "user_id"),
        ("test_scenarios", "user_id"),
        ("test_suites", "user_id"),
        ("ui_cases", "user_id"),
        ("ui_suites", "user_id"),
        ("ui_runs", "user_id"),
        ("ui_case_groups", "user_id"),
        ("users", "id"),
    ]:
        if table not in _tables(bind):
            continue
        if col not in _columns(bind, table):
            continue
        rows = bind.execute(sa.text(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL")).fetchall()
        for (uid,) in rows:
            try:
                user_ids.add(int(uid))
            except (TypeError, ValueError):
                continue

    # Also collect masqueraded project_id values that equal user ids on feature tables
    feature_tables = [
        "visual_baselines",
        "visual_comparisons",
        "trace_sessions",
        "ui_pages",
        "ui_elements",
        "healing_records",
        "case_concurrency_tags",
        "flaky_test_records",
        "openapi_snapshots",
        "api_contract_rules",
        "api_health_monitors",
    ]
    for table in feature_tables:
        if table not in _tables(bind) or "project_id" not in _columns(bind, table):
            continue
        rows = bind.execute(sa.text(f"SELECT DISTINCT project_id FROM {table} WHERE project_id IS NOT NULL")).fetchall()
        for (pid,) in rows:
            try:
                user_ids.add(int(pid))
            except (TypeError, ValueError):
                continue

    for uid in sorted(user_ids):
        if uid <= 0:
            continue
        key = f"personal-{uid}"
        existing = bind.execute(
            sa.text("SELECT id FROM workspace_projects WHERE key = :k"), {"k": key}
        ).fetchone()
        if existing:
            project_id = int(existing[0])
        else:
            bind.execute(
                sa.text(
                    "INSERT INTO workspace_projects (name, key, description, owner_id, is_personal) "
                    "VALUES (:name, :key, :desc, :owner_id, TRUE)"
                ),
                {
                    "name": "个人项目",
                    "key": key,
                    "desc": "兼容迁移自动创建的个人工作区",
                    "owner_id": uid,
                },
            )
            row = bind.execute(
                sa.text("SELECT id FROM workspace_projects WHERE key = :k"), {"k": key}
            ).fetchone()
            project_id = int(row[0])
        mem = bind.execute(
            sa.text(
                "SELECT id FROM workspace_project_members WHERE project_id = :p AND user_id = :u"
            ),
            {"p": project_id, "u": uid},
        ).fetchone()
        if not mem:
            bind.execute(
                sa.text(
                    "INSERT INTO workspace_project_members (project_id, user_id, role) "
                    "VALUES (:p, :u, 'owner')"
                ),
                {"p": project_id, "u": uid},
            )

        # Map user_id -> personal project on assets missing project_id
        for table in asset_tables_project_id:
            if table not in _tables(bind) or "user_id" not in _columns(bind, table):
                continue
            if "project_id" not in _columns(bind, table):
                continue
            bind.execute(
                sa.text(
                    f"UPDATE {table} SET project_id = :pid "
                    f"WHERE user_id = :uid AND (project_id IS NULL OR project_id = :uid)"
                ),
                {"pid": project_id, "uid": uid},
            )

        if "test_scenarios" in _tables(bind) and "workspace_project_id" in _columns(bind, "test_scenarios"):
            bind.execute(
                sa.text(
                    "UPDATE test_scenarios SET workspace_project_id = :pid "
                    "WHERE user_id = :uid AND workspace_project_id IS NULL"
                ),
                {"pid": project_id, "uid": uid},
            )

        for table in ("ui_cases", "ui_suites", "ui_runs"):
            if table not in _tables(bind) or "project_id" not in _columns(bind, table):
                continue
            bind.execute(
                sa.text(
                    f"UPDATE {table} SET project_id = :pid "
                    f"WHERE user_id = :uid AND (project_id IS NULL OR project_id = :uid)"
                ),
                {"pid": project_id, "uid": uid},
            )

        # Remap feature_upgrades masquerade project_id = user_id
        for table in feature_tables:
            if table not in _tables(bind) or "project_id" not in _columns(bind, table):
                continue
            bind.execute(
                sa.text(f"UPDATE {table} SET project_id = :pid WHERE project_id = :uid"),
                {"pid": project_id, "uid": uid},
            )


def downgrade() -> None:
    bind = op.get_bind()
    # Keep columns for safety; only drop workspace tables if present.
    if "workspace_project_members" in _tables(bind):
        op.drop_table("workspace_project_members")
    if "workspace_projects" in _tables(bind):
        op.drop_table("workspace_projects")
