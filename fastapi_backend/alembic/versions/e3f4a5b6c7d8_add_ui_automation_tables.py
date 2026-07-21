"""add UI automation tables

Revision ID: e3f4a5b6c7d8
Revises: c2d3e4f5a6b7, d2e3f4a5b6c7
Create Date: 2026-07-13

鏂板 UI 鑷姩鍖栨ā鍧楃殑 8 寮犺〃锛圫ection 6 of the Implementation Spec锛?
- ui_case_groups: 鐢ㄤ緥鍒嗙粍锛堟爲褰㈠眰绾э級
- ui_cases: UI 娴嬭瘯鐢ㄤ緥
- ui_case_versions: 鐢ㄤ緥鐗堟湰蹇収锛堜笉鍙彉锛?
- ui_steps: 鍙紪杈戞楠わ紙杩愯鏃朵娇鐢ㄧ増鏈揩鐓э級
- ui_suites: 娴嬭瘯濂椾欢
- ui_suite_items: 濂椾欢鏉＄洰
- ui_runs: 鎵ц杩愯璁板綍
- ui_step_results: 姝ラ鎵ц缁撴灉
- desktop_agents: 妗岄潰 Agent 娉ㄥ唽
- ui_artifacts: 浜х墿鍏冩暟鎹?
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migrations must remain runnable before the application package is importable.
# Keep the database-specific JSONB behaviour without importing runtime models.
JSONColumn = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


# revision identifiers, used by Alembic.
revision = "e3f4a5b6c7d8"
down_revision = ("c2d3e4f5a6b7", "d2e3f4a5b6c7")
branch_labels = None
depends_on = None


def upgrade():
    # 1. ui_case_groups (must exist before ui_cases FK)
    op.create_table(
        "ui_case_groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("ui_case_groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_ui_case_groups_parent_id", "ui_case_groups", ["parent_id"])
    op.create_index("idx_ui_case_groups_user_id", "ui_case_groups", ["user_id"])

    # 2. ui_case_versions (must exist before ui_cases FK to current_version_id)
    #    We create it without the FK to ui_cases first, then add it after ui_cases.
    #    Actually, we need to create ui_cases first for the case_id FK. Let's use
    #    a deferred approach: create ui_cases without current_version_id FK,
    #    then create ui_case_versions with FK to ui_cases, then add the FK back.
    #    Simpler: create ui_cases first with nullable FK, then versions.

    # 2a. ui_cases
    op.create_table(
        "ui_cases",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, nullable=True),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("ui_case_groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("owner_id", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("tags", JSONColumn, nullable=True),
        sa.Column("base_url", sa.Text, nullable=True),
        sa.Column("default_timeout_ms", sa.Integer, nullable=False, server_default="10000"),
        sa.Column("navigation_timeout_ms", sa.Integer, nullable=False, server_default="30000"),
        sa.Column("viewport", JSONColumn, nullable=True),
        sa.Column("locale", sa.String(20), nullable=True),
        sa.Column("timezone_id", sa.String(50), nullable=True),
        sa.Column("color_scheme", sa.String(20), nullable=True),
        sa.Column("storage_state_ref", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("current_version_id", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_ui_cases_user_id", "ui_cases", ["user_id"])
    op.create_index("idx_ui_cases_project_id", "ui_cases", ["project_id"])
    op.create_index("idx_ui_cases_group_id", "ui_cases", ["group_id"])
    op.create_index("idx_ui_cases_status", "ui_cases", ["status"])

    # 2b. ui_case_versions
    op.create_table(
        "ui_case_versions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.Integer, sa.ForeignKey("ui_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("snapshot_json", JSONColumn, nullable=False),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("created_by", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("case_id", "version_number", name="uq_ui_case_version_number"),
    )
    op.create_index("idx_ui_case_versions_case_id", "ui_case_versions", ["case_id"])

    # Add FK from ui_cases.current_version_id -> ui_case_versions.id
    op.create_foreign_key(
        "fk_ui_cases_current_version_id",
        "ui_cases",
        "ui_case_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 3. ui_steps
    op.create_table(
        "ui_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.Integer, sa.ForeignKey("ui_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order", sa.Integer, nullable=False, server_default="10"),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("breakpoint", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("locator", JSONColumn, nullable=True),
        sa.Column("input", JSONColumn, nullable=True),
        sa.Column("timeout_ms", sa.Integer, nullable=True),
        sa.Column("retry", JSONColumn, nullable=True),
        sa.Column("continue_on_failure", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("screenshot", sa.String(20), nullable=True, server_default="on-failure"),
        sa.Column("condition", sa.Text, nullable=True),
        sa.Column("children", JSONColumn, nullable=True),
    )
    op.create_index("idx_ui_steps_case_id", "ui_steps", ["case_id"])
    op.create_index("idx_ui_steps_order", "ui_steps", ["case_id", "order"])

    # 4. ui_suites
    op.create_table(
        "ui_suites",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("stop_on_first_failure", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_ui_suites_user_id", "ui_suites", ["user_id"])
    op.create_index("idx_ui_suites_project_id", "ui_suites", ["project_id"])

    # 5. ui_suite_items
    op.create_table(
        "ui_suite_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("ui_suites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.Integer, sa.ForeignKey("ui_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pinned_version_id", sa.Integer, sa.ForeignKey("ui_case_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("order", sa.Integer, nullable=False, server_default="10"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("data_source", JSONColumn, nullable=True),
        sa.Column("overrides", JSONColumn, nullable=True),
    )
    op.create_index("idx_ui_suite_items_suite_id", "ui_suite_items", ["suite_id"])

    # 6. desktop_agents
    op.create_table(
        "desktop_agents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_key", sa.String(36), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("owner_id", sa.Integer, nullable=False),
        sa.Column("team_id", sa.Integer, nullable=True),
        sa.Column("hostname", sa.String(200), nullable=True),
        sa.Column("os_version", sa.String(100), nullable=True),
        sa.Column("desktop_version", sa.String(50), nullable=True),
        sa.Column("capabilities", JSONColumn, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="offline"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_parallel", sa.Integer, nullable=False, server_default="1"),
        sa.Column("current_runs", sa.Integer, nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_desktop_agents_agent_key", "desktop_agents", ["agent_key"], unique=True)
    op.create_index("idx_desktop_agents_status", "desktop_agents", ["status"])

    # 7. ui_runs
    op.create_table(
        "ui_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_key", sa.String(36), nullable=False),
        sa.Column("project_id", sa.Integer, nullable=True),
        sa.Column("case_id", sa.Integer, sa.ForeignKey("ui_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("case_version_id", sa.Integer, sa.ForeignKey("ui_case_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("ui_suites.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_id", sa.Integer, sa.ForeignKey("desktop_agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("client_run_key", sa.String(64), nullable=True),
        sa.Column("trigger_type", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("triggered_by", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("browser", sa.String(20), nullable=True),
        sa.Column("browser_version", sa.String(50), nullable=True),
        sa.Column("desktop_version", sa.String(50), nullable=True),
        sa.Column("engine_version", sa.String(50), nullable=True),
        sa.Column("environment_id", sa.Integer, nullable=True),
        sa.Column("dataset_iteration", sa.Integer, nullable=True),
        sa.Column("retry_of_run_id", sa.Integer, sa.ForeignKey("ui_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("total_steps", sa.Integer, nullable=False, server_default="0"),
        sa.Column("passed_steps", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_steps", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_steps", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_summary", sa.Text, nullable=True),
        sa.Column("artifact_manifest", JSONColumn, nullable=True),
        sa.Column("user_id", sa.Integer, nullable=False),
    )
    op.create_index("idx_ui_runs_run_key", "ui_runs", ["run_key"], unique=True)
    op.create_index("idx_ui_runs_user_id", "ui_runs", ["user_id"])
    op.create_index("idx_ui_runs_project_id", "ui_runs", ["project_id"])
    op.create_index("idx_ui_runs_status", "ui_runs", ["status"])
    op.create_index("idx_ui_runs_agent_id", "ui_runs", ["agent_id"])
    op.create_index("idx_ui_runs_user_client_run_key", "ui_runs", ["user_id", "client_run_key"], unique=True)

    # 8. ui_step_results
    op.create_table(
        "ui_step_results",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("ui_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_id", sa.String(36), nullable=False),
        sa.Column("iteration", sa.Integer, nullable=False, server_default="0"),
        sa.Column("attempt", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("resolved_locator", sa.Text, nullable=True),
        sa.Column("input_preview", sa.Text, nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("screenshot_artifact_id", sa.Integer, nullable=True),
        sa.Column("trace_event_ref", sa.String(200), nullable=True),
    )
    op.create_index("idx_ui_step_results_run_id", "ui_step_results", ["run_id"])
    op.create_index("idx_ui_step_results_step_id", "ui_step_results", ["step_id"])

    # 9. ui_artifacts
    op.create_table(
        "ui_artifacts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("ui_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("storage_type", sa.String(20), nullable=False, server_default="local"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_ui_artifacts_run_id", "ui_artifacts", ["run_id"])
    op.create_index("idx_ui_artifacts_type", "ui_artifacts", ["type"])


def downgrade():
    op.drop_table("ui_artifacts")
    op.drop_table("ui_step_results")
    op.drop_table("ui_runs")
    op.drop_table("desktop_agents")
    op.drop_table("ui_suite_items")
    op.drop_table("ui_suites")
    op.drop_table("ui_steps")
    op.drop_table("ui_case_versions")
    op.drop_table("ui_cases")
    op.drop_table("ui_case_groups")

