"""add feature upgrade tables

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-07-24 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    return name in sa.inspect(bind).get_table_names()


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_table(bind, "api_health_monitors"):
        op.create_table(
            "api_health_monitors",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("environment_id", sa.Integer(), nullable=False),
            sa.Column("interval_seconds", sa.Integer(), nullable=False),
            sa.Column("timeout_ms", sa.Integer(), nullable=False),
            sa.Column("expected_status", sa.Integer(), nullable=False),
            sa.Column("max_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("alert_consecutive_failures", sa.Integer(), nullable=False),
            sa.Column("alert_response_time_degradation", sa.Float(), nullable=True),
            sa.Column("notification_channel_id", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("last_check_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_status", sa.String(length=10), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_api_health_monitors_project", "api_health_monitors", ["project_id"])
        op.create_index("ix_api_health_monitors_project_id", "api_health_monitors", ["project_id"])

    if not _has_table(bind, "case_concurrency_tags"):
        op.create_table(
            "case_concurrency_tags",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("tag", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("max_concurrent", sa.Integer(), nullable=False),
            sa.UniqueConstraint("project_id", "tag", name="uq_case_concurrency_tag"),
        )
        op.create_index("ix_case_concurrency_tags_project_id", "case_concurrency_tags", ["project_id"])

    if not _has_table(bind, "case_reviews"):
        op.create_table(
            "case_reviews",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("case_type", sa.String(length=10), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("case_version", sa.Integer(), nullable=True),
            sa.Column("state", sa.String(length=20), nullable=False),
            sa.Column("submitted_by", sa.Integer(), nullable=False),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("required_approvals", sa.Integer(), nullable=False),
            sa.Column("current_approvals", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_case_reviews_project", "case_reviews", ["project_id"])
        op.create_index("ix_case_reviews_project_id", "case_reviews", ["project_id"])
        op.create_index("idx_case_reviews_state", "case_reviews", ["state"])

    if not _has_table(bind, "defect_tracker_configs"):
        op.create_table(
            "defect_tracker_configs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("tracker_type", sa.String(length=20), nullable=False),
            sa.Column("base_url", sa.String(length=500), nullable=False),
            sa.Column("credentials_encrypted", sa.Text(), nullable=False),
            sa.Column("project_key", sa.String(length=100), nullable=True),
            sa.Column("custom_fields_mapping", sa.JSON(), nullable=True),
            sa.Column("default_issue_type", sa.String(length=50), nullable=True),
            sa.Column("default_priority", sa.String(length=20), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_defect_tracker_configs_project_id", "defect_tracker_configs", ["project_id"])
        op.create_index("idx_defect_tracker_configs_project", "defect_tracker_configs", ["project_id"])

    if not _has_table(bind, "execution_progress"):
        op.create_table(
            "execution_progress",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("suite_execution_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("total_cases", sa.Integer(), nullable=False),
            sa.Column("completed_cases", sa.Integer(), nullable=False),
            sa.Column("passed_cases", sa.Integer(), nullable=False),
            sa.Column("failed_cases", sa.Integer(), nullable=False),
            sa.Column("running_cases", sa.Integer(), nullable=False),
            sa.Column("skipped_cases", sa.Integer(), nullable=False),
            sa.Column("estimated_remaining_ms", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("suite_execution_id", name="uq_execution_progress_suite_execution_id"),
            sa.UniqueConstraint("suite_execution_id", name="uq_execution_progress_execution"),
        )

    if not _has_table(bind, "flaky_detection_configs"):
        op.create_table(
            "flaky_detection_configs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("window_size", sa.Integer(), nullable=False),
            sa.Column("flaky_high_threshold", sa.Float(), nullable=False),
            sa.Column("flaky_low_threshold", sa.Float(), nullable=False),
            sa.Column("auto_quarantine", sa.Boolean(), nullable=False),
            sa.Column("auto_quarantine_score", sa.Float(), nullable=False),
            sa.Column("alert_on_new_flaky", sa.Boolean(), nullable=False),
            sa.Column("notification_channel_id", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("project_id", name="uq_flaky_detection_configs_project_id"),
            sa.UniqueConstraint("project_id", name="uq_flaky_detection_config_project"),
        )

    if not _has_table(bind, "flaky_test_records"):
        op.create_table(
            "flaky_test_records",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("case_type", sa.String(length=10), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("case_name", sa.String(length=200), nullable=False),
            sa.Column("recent_results", sa.JSON(), nullable=False),
            sa.Column("total_runs", sa.Integer(), nullable=False),
            sa.Column("pass_count", sa.Integer(), nullable=False),
            sa.Column("fail_count", sa.Integer(), nullable=False),
            sa.Column("status_changes", sa.Integer(), nullable=False),
            sa.Column("flaky_score", sa.Float(), nullable=False),
            sa.Column("classification", sa.String(length=20), nullable=False),
            sa.Column("is_quarantined", sa.Boolean(), nullable=False),
            sa.Column("quarantined_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("quarantined_by", sa.Integer(), nullable=True),
            sa.Column("last_status_change_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("project_id", "case_type", "case_id", name="uq_flaky_test_case"),
        )
        op.create_index("idx_flaky_test_records_score", "flaky_test_records", ["flaky_score"])
        op.create_index("idx_flaky_test_records_project", "flaky_test_records", ["project_id"])
        op.create_index("ix_flaky_test_records_project_id", "flaky_test_records", ["project_id"])

    if not _has_table(bind, "healing_configs"):
        op.create_table(
            "healing_configs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("auto_apply_threshold", sa.Float(), nullable=False),
            sa.Column("suggest_threshold", sa.Float(), nullable=False),
            sa.Column("use_llm", sa.Boolean(), nullable=False),
            sa.Column("llm_model", sa.String(length=50), nullable=True),
            sa.Column("max_candidates", sa.Integer(), nullable=False),
            sa.Column("capture_dom_on_failure", sa.Boolean(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("project_id", name="uq_healing_configs_project_id"),
            sa.UniqueConstraint("project_id", name="uq_healing_config_project"),
        )

    if not _has_table(bind, "openapi_snapshots"):
        op.create_table(
            "openapi_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("group_id", sa.Integer(), nullable=True),
            sa.Column("source_url", sa.String(length=1000), nullable=True),
            sa.Column("source_type", sa.String(length=20), nullable=False),
            sa.Column("spec_version", sa.String(length=50), nullable=True),
            sa.Column("content_hash", sa.String(length=64), nullable=False),
            sa.Column("spec_content", sa.Text(), nullable=False),
            sa.Column("parsed_endpoints", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_openapi_snapshots_project_id", "openapi_snapshots", ["project_id"])
        op.create_index("idx_openapi_snapshots_project", "openapi_snapshots", ["project_id"])

    if not _has_table(bind, "proto_files"):
        op.create_table(
            "proto_files",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("file_path", sa.String(length=500), nullable=False),
            sa.Column("content_hash", sa.String(length=64), nullable=False),
            sa.Column("package_name", sa.String(length=200), nullable=True),
            sa.Column("services", sa.JSON(), nullable=True),
            sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("parse_error", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_proto_files_project", "proto_files", ["project_id"])
        op.create_index("ix_proto_files_project_id", "proto_files", ["project_id"])

    if not _has_table(bind, "report_templates"):
        op.create_table(
            "report_templates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("logo_path", sa.String(length=500), nullable=True),
            sa.Column("primary_color", sa.String(length=20), nullable=False),
            sa.Column("company_name", sa.String(length=200), nullable=True),
            sa.Column("footer_text", sa.String(length=500), nullable=True),
            sa.Column("sections", sa.JSON(), nullable=False),
            sa.Column("custom_fields", sa.JSON(), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_report_templates_project", "report_templates", ["project_id"])
        op.create_index("ix_report_templates_project_id", "report_templates", ["project_id"])

    if not _has_table(bind, "requirements"):
        op.create_table(
            "requirements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("external_id", sa.String(length=100), nullable=True),
            sa.Column("external_url", sa.String(length=500), nullable=True),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("priority", sa.String(length=20), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("sprint", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_requirements_project", "requirements", ["project_id"])
        op.create_index("ix_requirements_project_id", "requirements", ["project_id"])

    if not _has_table(bind, "scenario_flow_graphs"):
        op.create_table(
            "scenario_flow_graphs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("scenario_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("nodes", sa.JSON(), nullable=False),
            sa.Column("edges", sa.JSON(), nullable=False),
            sa.Column("viewport", sa.JSON(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("scenario_id", name="uq_scenario_flow_graphs_scenario_id"),
            sa.UniqueConstraint("scenario_id", name="uq_scenario_flow_graph"),
        )

    if not _has_table(bind, "ui_network_rules"):
        op.create_table(
            "ui_network_rules",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("url_pattern", sa.String(length=1000), nullable=False),
            sa.Column("pattern_type", sa.String(length=10), nullable=False),
            sa.Column("method_filter", sa.String(length=20), nullable=True),
            sa.Column("resource_type", sa.String(length=30), nullable=True),
            sa.Column("action", sa.String(length=20), nullable=False),
            sa.Column("fulfill_status", sa.Integer(), nullable=True),
            sa.Column("fulfill_headers", sa.JSON(), nullable=True),
            sa.Column("fulfill_body", sa.Text(), nullable=True),
            sa.Column("fulfill_content_type", sa.String(length=100), nullable=True),
            sa.Column("modify_headers", sa.JSON(), nullable=True),
            sa.Column("modify_body_jsonpath", sa.JSON(), nullable=True),
            sa.Column("delay_ms", sa.Integer(), nullable=True),
            sa.Column("abort_reason", sa.String(length=50), nullable=True),
            sa.Column("source", sa.String(length=20), nullable=False),
            sa.Column("mock_rule_id", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_ui_network_rules_project_id", "ui_network_rules", ["project_id"])
        op.create_index("idx_ui_network_rules_project", "ui_network_rules", ["project_id"])

    if not _has_table(bind, "ui_pages"):
        op.create_table(
            "ui_pages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("url_pattern", sa.String(length=500), nullable=True),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["parent_id"], ["ui_pages.id"], ondelete="SET NULL"),
        )
        op.create_index("idx_ui_pages_parent", "ui_pages", ["parent_id"])
        op.create_index("ix_ui_pages_project_id", "ui_pages", ["project_id"])
        op.create_index("idx_ui_pages_project", "ui_pages", ["project_id"])

    if not _has_table(bind, "visual_comparison_configs"):
        op.create_table(
            "visual_comparison_configs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("default_threshold", sa.Float(), nullable=False),
            sa.Column("antialiasing_tolerance", sa.Float(), nullable=False),
            sa.Column("auto_approve_below", sa.Float(), nullable=False),
            sa.Column("auto_reject_above", sa.Float(), nullable=False),
            sa.Column("default_engine", sa.String(length=20), nullable=False),
            sa.Column("capture_full_page", sa.Boolean(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("project_id", name="uq_visual_comparison_configs_project_id"),
            sa.UniqueConstraint("project_id", name="uq_visual_comparison_config_project"),
        )

    if not _has_table(bind, "ws_session_logs"):
        op.create_table(
            "ws_session_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("history_id", sa.Integer(), nullable=False),
            sa.Column("direction", sa.String(length=10), nullable=False),
            sa.Column("frame_type", sa.String(length=10), nullable=False),
            sa.Column("payload_preview", sa.Text(), nullable=True),
            sa.Column("payload_size", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_ws_session_logs_history", "ws_session_logs", ["history_id"])
        op.create_index("ix_ws_session_logs_history_id", "ws_session_logs", ["history_id"])

    if not _has_table(bind, "api_contract_rules"):
        op.create_table(
            "api_contract_rules",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("snapshot_id", sa.Integer(), nullable=False),
            sa.Column("endpoint_path", sa.String(length=500), nullable=False),
            sa.Column("method", sa.String(length=10), nullable=False),
            sa.Column("validate_request", sa.Boolean(), nullable=False),
            sa.Column("validate_response", sa.Boolean(), nullable=False),
            sa.Column("strict_mode", sa.Boolean(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["snapshot_id"], ["openapi_snapshots.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_api_contract_rules_project", "api_contract_rules", ["project_id"])
        op.create_index("ix_api_contract_rules_project_id", "api_contract_rules", ["project_id"])

    if not _has_table(bind, "api_health_check_results"):
        op.create_table(
            "api_health_check_results",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("monitor_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=10), nullable=False),
            sa.Column("response_time_ms", sa.Integer(), nullable=True),
            sa.Column("status_code", sa.Integer(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["monitor_id"], ["api_health_monitors.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_api_health_check_results_checked", "api_health_check_results", ["checked_at"])
        op.create_index("ix_api_health_check_results_checked_at", "api_health_check_results", ["checked_at"])
        op.create_index("idx_api_health_check_results_monitor", "api_health_check_results", ["monitor_id"])

    if not _has_table(bind, "case_review_actions"):
        op.create_table(
            "case_review_actions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("review_id", sa.Integer(), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=False),
            sa.Column("action", sa.String(length=20), nullable=False),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["review_id"], ["case_reviews.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_case_review_actions_review", "case_review_actions", ["review_id"])

    if not _has_table(bind, "case_review_comments"):
        op.create_table(
            "case_review_comments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("review_id", sa.Integer(), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("step_id", sa.String(length=36), nullable=True),
            sa.Column("is_resolved", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["review_id"], ["case_reviews.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_case_review_comments_review", "case_review_comments", ["review_id"])

    if not _has_table(bind, "defect_records"):
        op.create_table(
            "defect_records",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("tracker_config_id", sa.Integer(), nullable=True),
            sa.Column("external_id", sa.String(length=100), nullable=True),
            sa.Column("external_url", sa.String(length=500), nullable=True),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("priority", sa.String(length=20), nullable=True),
            sa.Column("severity", sa.String(length=20), nullable=True),
            sa.Column("source_type", sa.String(length=20), nullable=False),
            sa.Column("source_run_id", sa.Integer(), nullable=True),
            sa.Column("source_step_result_id", sa.Integer(), nullable=True),
            sa.Column("attachments", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tracker_config_id"], ["defect_tracker_configs.id"], ondelete="SET NULL"),
        )
        op.create_index("idx_defect_records_project", "defect_records", ["project_id"])
        op.create_index("idx_defect_records_status", "defect_records", ["status"])
        op.create_index("ix_defect_records_project_id", "defect_records", ["project_id"])

    if not _has_table(bind, "requirement_case_links"):
        op.create_table(
            "requirement_case_links",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("requirement_id", sa.Integer(), nullable=False),
            sa.Column("case_type", sa.String(length=10), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("coverage_type", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("requirement_id", "case_type", "case_id", name="uq_requirement_case_link"),
        )
        op.create_index("ix_requirement_case_links_requirement_id", "requirement_case_links", ["requirement_id"])

    if not _has_table(bind, "schema_change_records"):
        op.create_table(
            "schema_change_records",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("old_snapshot_id", sa.Integer(), nullable=False),
            sa.Column("new_snapshot_id", sa.Integer(), nullable=False),
            sa.Column("changes", sa.JSON(), nullable=False),
            sa.Column("breaking_changes", sa.JSON(), nullable=False),
            sa.Column("is_breaking", sa.Boolean(), nullable=False),
            sa.Column("notified", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["old_snapshot_id"], ["openapi_snapshots.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["new_snapshot_id"], ["openapi_snapshots.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_schema_change_records_project", "schema_change_records", ["project_id"])
        op.create_index("ix_schema_change_records_project_id", "schema_change_records", ["project_id"])

    if not _has_table(bind, "suite_shards"):
        op.create_table(
            "suite_shards",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("suite_execution_id", sa.Integer(), nullable=False),
            sa.Column("suite_id", sa.Integer(), nullable=True),
            sa.Column("shard_index", sa.Integer(), nullable=False),
            sa.Column("total_shards", sa.Integer(), nullable=False),
            sa.Column("assigned_agent_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("case_ids", sa.JSON(), nullable=False),
            sa.Column("total_cases", sa.Integer(), nullable=False),
            sa.Column("completed_cases", sa.Integer(), nullable=False),
            sa.Column("passed_cases", sa.Integer(), nullable=False),
            sa.Column("failed_cases", sa.Integer(), nullable=False),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("original_agent_id", sa.Integer(), nullable=True),
            sa.Column("reassign_count", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["assigned_agent_id"], ["desktop_agents.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["suite_id"], ["ui_suites.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("suite_execution_id", "shard_index", name="uq_suite_shard_index"),
        )
        op.create_index("ix_suite_shards_suite_execution_id", "suite_shards", ["suite_execution_id"])
        op.create_index("idx_suite_shards_execution", "suite_shards", ["suite_execution_id"])
        op.create_index("idx_suite_shards_agent", "suite_shards", ["assigned_agent_id"])
        op.create_index("idx_suite_shards_status", "suite_shards", ["status"])

    if not _has_table(bind, "ui_elements"):
        op.create_table(
            "ui_elements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("page_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("locators", sa.JSON(), nullable=False),
            sa.Column("frame_path", sa.JSON(), nullable=True),
            sa.Column("thumbnail_path", sa.String(length=500), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("usage_count", sa.Integer(), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("heal_count", sa.Integer(), nullable=False),
            sa.Column("is_deprecated", sa.Boolean(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["page_id"], ["ui_pages.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_ui_elements_page", "ui_elements", ["page_id"])
        op.create_index("ix_ui_elements_project_id", "ui_elements", ["project_id"])
        op.create_index("idx_ui_elements_project", "ui_elements", ["project_id"])

    if not _has_table(bind, "ui_network_rule_assignments"):
        op.create_table(
            "ui_network_rule_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("rule_id", sa.Integer(), nullable=False),
            sa.Column("target_type", sa.String(length=10), nullable=False),
            sa.Column("target_id", sa.Integer(), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["rule_id"], ["ui_network_rules.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("rule_id", "target_type", "target_id", name="uq_ui_network_rule_assignment"),
        )

    if not _has_table(bind, "case_concurrency_tag_assignments"):
        op.create_table(
            "case_concurrency_tag_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("tag_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["case_id"], ["ui_cases.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tag_id"], ["case_concurrency_tags.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("case_id", "tag_id", name="uq_case_concurrency_assignment"),
        )
        op.create_index("ix_case_concurrency_tag_assignments_case_id", "case_concurrency_tag_assignments", ["case_id"])

    if not _has_table(bind, "defect_case_links"):
        op.create_table(
            "defect_case_links",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("defect_id", sa.Integer(), nullable=False),
            sa.Column("case_type", sa.String(length=10), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("linked_by", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["defect_id"], ["defect_records.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("defect_id", "case_type", "case_id", name="uq_defect_case_link"),
        )
        op.create_index("ix_defect_case_links_defect_id", "defect_case_links", ["defect_id"])

    if not _has_table(bind, "protocol_request_configs"):
        op.create_table(
            "protocol_request_configs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("case_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("protocol", sa.String(length=20), nullable=False),
            sa.Column("grpc_proto_file_id", sa.Integer(), nullable=True),
            sa.Column("grpc_service", sa.String(length=200), nullable=True),
            sa.Column("grpc_method", sa.String(length=200), nullable=True),
            sa.Column("grpc_metadata", sa.JSON(), nullable=True),
            sa.Column("grpc_request_body", sa.Text(), nullable=True),
            sa.Column("grpc_use_reflection", sa.Boolean(), nullable=False),
            sa.Column("grpc_deadline_ms", sa.Integer(), nullable=False),
            sa.Column("grpc_tls_enabled", sa.Boolean(), nullable=False),
            sa.Column("grpc_tls_cert_path", sa.String(length=500), nullable=True),
            sa.Column("ws_url", sa.String(length=2000), nullable=True),
            sa.Column("ws_headers", sa.JSON(), nullable=True),
            sa.Column("ws_subprotocols", sa.JSON(), nullable=True),
            sa.Column("ws_connect_timeout_ms", sa.Integer(), nullable=False),
            sa.Column("ws_messages", sa.JSON(), nullable=True),
            sa.Column("sse_url", sa.String(length=2000), nullable=True),
            sa.Column("sse_headers", sa.JSON(), nullable=True),
            sa.Column("sse_event_types", sa.JSON(), nullable=True),
            sa.Column("sse_max_events", sa.Integer(), nullable=False),
            sa.Column("sse_timeout_ms", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["case_id"], ["api_cases.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["grpc_proto_file_id"], ["proto_files.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("case_id", name="uq_protocol_request_config_case"),
            sa.UniqueConstraint("case_id", name="uq_protocol_request_configs_case_id"),
        )

    if not _has_table(bind, "ui_step_element_refs"):
        op.create_table(
            "ui_step_element_refs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("step_id", sa.String(length=36), nullable=False),
            sa.Column("element_id", sa.Integer(), nullable=False),
            sa.Column("override_locators", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["element_id"], ["ui_elements.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("step_id", "element_id", name="uq_ui_step_element_ref"),
        )
        op.create_index("ix_ui_step_element_refs_step_id", "ui_step_element_refs", ["step_id"])
        op.create_index("idx_ui_step_element_refs_element", "ui_step_element_refs", ["element_id"])
        op.create_index("idx_ui_step_element_refs_step", "ui_step_element_refs", ["step_id"])

    if not _has_table(bind, "agent_worker_slots"):
        op.create_table(
            "agent_worker_slots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("agent_id", sa.Integer(), nullable=False),
            sa.Column("slot_index", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("current_run_id", sa.Integer(), nullable=True),
            sa.Column("current_case_name", sa.String(length=200), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["agent_id"], ["desktop_agents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["current_run_id"], ["ui_runs.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("agent_id", "slot_index", name="uq_agent_worker_slot"),
        )
        op.create_index("ix_agent_worker_slots_agent_id", "agent_worker_slots", ["agent_id"])

    if not _has_table(bind, "healing_records"):
        op.create_table(
            "healing_records",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("element_id", sa.Integer(), nullable=True),
            sa.Column("run_id", sa.Integer(), nullable=True),
            sa.Column("step_result_id", sa.Integer(), nullable=True),
            sa.Column("original_locator", sa.JSON(), nullable=False),
            sa.Column("failure_reason", sa.Text(), nullable=False),
            sa.Column("page_url", sa.String(length=2000), nullable=True),
            sa.Column("dom_snapshot_path", sa.String(length=500), nullable=True),
            sa.Column("healed_locator", sa.JSON(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("strategy_used", sa.String(length=100), nullable=True),
            sa.Column("candidates", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["ui_runs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["element_id"], ["ui_elements.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_healing_records_element", "healing_records", ["element_id"])
        op.create_index("idx_healing_records_run", "healing_records", ["run_id"])
        op.create_index("idx_healing_records_project", "healing_records", ["project_id"])
        op.create_index("ix_healing_records_project_id", "healing_records", ["project_id"])

    if not _has_table(bind, "trace_sessions"):
        op.create_table(
            "trace_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("run_id", sa.Integer(), nullable=False),
            sa.Column("step_result_id", sa.Integer(), nullable=True),
            sa.Column("file_path", sa.String(length=500), nullable=False),
            sa.Column("file_size_bytes", sa.Integer(), nullable=False),
            sa.Column("file_hash", sa.String(length=64), nullable=False),
            sa.Column("parsed", sa.Boolean(), nullable=False),
            sa.Column("action_count", sa.Integer(), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("browser_version", sa.String(length=50), nullable=True),
            sa.Column("parse_cache", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["ui_runs.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_trace_sessions_project_id", "trace_sessions", ["project_id"])
        op.create_index("idx_trace_sessions_project", "trace_sessions", ["project_id"])
        op.create_index("idx_trace_sessions_run", "trace_sessions", ["run_id"])

    if not _has_table(bind, "visual_baselines"):
        op.create_table(
            "visual_baselines",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("ui_step_id", sa.String(length=36), nullable=False),
            sa.Column("environment_id", sa.Integer(), nullable=True),
            sa.Column("browser_engine", sa.String(length=20), nullable=False),
            sa.Column("viewport_width", sa.Integer(), nullable=False),
            sa.Column("viewport_height", sa.Integer(), nullable=False),
            sa.Column("device_pixel_ratio", sa.Float(), nullable=False),
            sa.Column("image_path", sa.String(length=500), nullable=False),
            sa.Column("image_hash", sa.String(length=64), nullable=False),
            sa.Column("image_width", sa.Integer(), nullable=False),
            sa.Column("image_height", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("captured_from_run_id", sa.Integer(), nullable=True),
            sa.Column("captured_from_step_result_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["captured_from_run_id"], ["ui_runs.id"], ondelete="SET NULL"),
        )
        op.create_index("idx_visual_baselines_project", "visual_baselines", ["project_id"])
        op.create_index("ix_visual_baselines_ui_step_id", "visual_baselines", ["ui_step_id"])
        op.create_index("idx_visual_baselines_step", "visual_baselines", ["ui_step_id"])
        op.create_index("ix_visual_baselines_project_id", "visual_baselines", ["project_id"])
        op.create_index("idx_visual_baselines_lookup", "visual_baselines", ["ui_step_id", "environment_id", "browser_engine", "viewport_width", "viewport_height", "status"])

    if not _has_table(bind, "visual_comparisons"):
        op.create_table(
            "visual_comparisons",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("run_id", sa.Integer(), nullable=False),
            sa.Column("step_result_id", sa.Integer(), nullable=True),
            sa.Column("ui_step_id", sa.String(length=36), nullable=True),
            sa.Column("baseline_id", sa.Integer(), nullable=True),
            sa.Column("actual_image_path", sa.String(length=500), nullable=False),
            sa.Column("diff_image_path", sa.String(length=500), nullable=True),
            sa.Column("diff_percentage", sa.Float(), nullable=False),
            sa.Column("threshold", sa.Float(), nullable=False),
            sa.Column("mismatched_pixels", sa.Integer(), nullable=False),
            sa.Column("total_pixels", sa.Integer(), nullable=False),
            sa.Column("verdict", sa.String(length=20), nullable=False),
            sa.Column("verdict_by", sa.Integer(), nullable=True),
            sa.Column("verdict_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verdict_comment", sa.Text(), nullable=True),
            sa.Column("config_snapshot", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["ui_runs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["baseline_id"], ["visual_baselines.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["step_result_id"], ["ui_step_results.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_visual_comparisons_ui_step_id", "visual_comparisons", ["ui_step_id"])
        op.create_index("idx_visual_comparisons_step_result", "visual_comparisons", ["step_result_id"])
        op.create_index("idx_visual_comparisons_run", "visual_comparisons", ["run_id"])
        op.create_index("idx_visual_comparisons_project", "visual_comparisons", ["project_id"])
        op.create_index("ix_visual_comparisons_project_id", "visual_comparisons", ["project_id"])

    if not _has_table(bind, "visual_mask_regions"):
        op.create_table(
            "visual_mask_regions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("baseline_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("x", sa.Float(), nullable=False),
            sa.Column("y", sa.Float(), nullable=False),
            sa.Column("width", sa.Float(), nullable=False),
            sa.Column("height", sa.Float(), nullable=False),
            sa.Column("shape", sa.String(length=20), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["baseline_id"], ["visual_baselines.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_visual_mask_regions_baseline", "visual_mask_regions", ["baseline_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "visual_mask_regions"):
        op.drop_table("visual_mask_regions")
    if _has_table(bind, "visual_comparisons"):
        op.drop_table("visual_comparisons")
    if _has_table(bind, "visual_baselines"):
        op.drop_table("visual_baselines")
    if _has_table(bind, "trace_sessions"):
        op.drop_table("trace_sessions")
    if _has_table(bind, "healing_records"):
        op.drop_table("healing_records")
    if _has_table(bind, "agent_worker_slots"):
        op.drop_table("agent_worker_slots")
    if _has_table(bind, "ui_step_element_refs"):
        op.drop_table("ui_step_element_refs")
    if _has_table(bind, "protocol_request_configs"):
        op.drop_table("protocol_request_configs")
    if _has_table(bind, "defect_case_links"):
        op.drop_table("defect_case_links")
    if _has_table(bind, "case_concurrency_tag_assignments"):
        op.drop_table("case_concurrency_tag_assignments")
    if _has_table(bind, "ui_network_rule_assignments"):
        op.drop_table("ui_network_rule_assignments")
    if _has_table(bind, "ui_elements"):
        op.drop_table("ui_elements")
    if _has_table(bind, "suite_shards"):
        op.drop_table("suite_shards")
    if _has_table(bind, "schema_change_records"):
        op.drop_table("schema_change_records")
    if _has_table(bind, "requirement_case_links"):
        op.drop_table("requirement_case_links")
    if _has_table(bind, "defect_records"):
        op.drop_table("defect_records")
    if _has_table(bind, "case_review_comments"):
        op.drop_table("case_review_comments")
    if _has_table(bind, "case_review_actions"):
        op.drop_table("case_review_actions")
    if _has_table(bind, "api_health_check_results"):
        op.drop_table("api_health_check_results")
    if _has_table(bind, "api_contract_rules"):
        op.drop_table("api_contract_rules")
    if _has_table(bind, "ws_session_logs"):
        op.drop_table("ws_session_logs")
    if _has_table(bind, "visual_comparison_configs"):
        op.drop_table("visual_comparison_configs")
    if _has_table(bind, "ui_pages"):
        op.drop_table("ui_pages")
    if _has_table(bind, "ui_network_rules"):
        op.drop_table("ui_network_rules")
    if _has_table(bind, "scenario_flow_graphs"):
        op.drop_table("scenario_flow_graphs")
    if _has_table(bind, "requirements"):
        op.drop_table("requirements")
    if _has_table(bind, "report_templates"):
        op.drop_table("report_templates")
    if _has_table(bind, "proto_files"):
        op.drop_table("proto_files")
    if _has_table(bind, "openapi_snapshots"):
        op.drop_table("openapi_snapshots")
    if _has_table(bind, "healing_configs"):
        op.drop_table("healing_configs")
    if _has_table(bind, "flaky_test_records"):
        op.drop_table("flaky_test_records")
    if _has_table(bind, "flaky_detection_configs"):
        op.drop_table("flaky_detection_configs")
    if _has_table(bind, "execution_progress"):
        op.drop_table("execution_progress")
    if _has_table(bind, "defect_tracker_configs"):
        op.drop_table("defect_tracker_configs")
    if _has_table(bind, "case_reviews"):
        op.drop_table("case_reviews")
    if _has_table(bind, "case_concurrency_tags"):
        op.drop_table("case_concurrency_tags")
    if _has_table(bind, "api_health_monitors"):
        op.drop_table("api_health_monitors")
