"""TestMaster feature-upgrade models (visual/element/parallel/flaky/defect/protocol/flow/review)."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from fastapi_backend.core.database import Base
from fastapi_backend.models.ui_automation import JSONColumn


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. Visual regression + Trace Viewer
# ---------------------------------------------------------------------------


class BaselineStatus(str, enum.Enum):
    active = "active"
    superseded = "superseded"
    pending = "pending"


class DiffVerdict(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    auto_passed = "auto_passed"
    no_baseline = "no_baseline"


class VisualBaseline(Base):
    __tablename__ = "visual_baselines"
    __table_args__ = (
        Index("idx_visual_baselines_project", "project_id"),
        Index("idx_visual_baselines_step", "ui_step_id"),
        Index(
            "idx_visual_baselines_lookup",
            "ui_step_id",
            "environment_id",
            "browser_engine",
            "viewport_width",
            "viewport_height",
            "status",
        ),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    ui_step_id = Column(String(36), nullable=False, index=True)
    environment_id = Column(Integer, nullable=True)
    browser_engine = Column(String(20), nullable=False, default="chromium")
    viewport_width = Column(Integer, nullable=False, default=1280)
    viewport_height = Column(Integer, nullable=False, default=720)
    device_pixel_ratio = Column(Float, nullable=False, default=1.0)
    image_path = Column(String(500), nullable=False)
    image_hash = Column(String(64), nullable=False)
    image_width = Column(Integer, nullable=False, default=0)
    image_height = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default=BaselineStatus.active.value)
    version = Column(Integer, nullable=False, default=1)
    captured_from_run_id = Column(Integer, ForeignKey("ui_runs.id", ondelete="SET NULL"), nullable=True)
    captured_from_step_result_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    masks = relationship("VisualMaskRegion", back_populates="baseline", cascade="all, delete-orphan")


class VisualMaskRegion(Base):
    __tablename__ = "visual_mask_regions"
    __table_args__ = (Index("idx_visual_mask_regions_baseline", "baseline_id"),)

    id = Column(Integer, primary_key=True)
    baseline_id = Column(Integer, ForeignKey("visual_baselines.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    shape = Column(String(20), nullable=False, default="rect")
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    baseline = relationship("VisualBaseline", back_populates="masks")


class VisualComparison(Base):
    __tablename__ = "visual_comparisons"
    __table_args__ = (
        Index("idx_visual_comparisons_project", "project_id"),
        Index("idx_visual_comparisons_run", "run_id"),
        Index("idx_visual_comparisons_step_result", "step_result_id"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("ui_runs.id", ondelete="CASCADE"), nullable=False)
    step_result_id = Column(Integer, ForeignKey("ui_step_results.id", ondelete="CASCADE"), nullable=True)
    ui_step_id = Column(String(36), nullable=True, index=True)
    baseline_id = Column(Integer, ForeignKey("visual_baselines.id", ondelete="SET NULL"), nullable=True)
    actual_image_path = Column(String(500), nullable=False)
    diff_image_path = Column(String(500), nullable=True)
    diff_percentage = Column(Float, nullable=False, default=0.0)
    threshold = Column(Float, nullable=False, default=0.1)
    mismatched_pixels = Column(Integer, nullable=False, default=0)
    total_pixels = Column(Integer, nullable=False, default=0)
    verdict = Column(String(20), nullable=False, default=DiffVerdict.pending.value)
    verdict_by = Column(Integer, nullable=True)
    verdict_at = Column(DateTime(timezone=True), nullable=True)
    verdict_comment = Column(Text, nullable=True)
    config_snapshot = Column(JSONColumn, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class VisualComparisonConfig(Base):
    __tablename__ = "visual_comparison_configs"
    __table_args__ = (UniqueConstraint("project_id", name="uq_visual_comparison_config_project"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, unique=True)
    default_threshold = Column(Float, nullable=False, default=0.1)
    antialiasing_tolerance = Column(Float, nullable=False, default=0.05)
    auto_approve_below = Column(Float, nullable=False, default=0.01)
    auto_reject_above = Column(Float, nullable=False, default=5.0)
    default_engine = Column(String(20), nullable=False, default="chromium")
    capture_full_page = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class TraceSession(Base):
    __tablename__ = "trace_sessions"
    __table_args__ = (
        Index("idx_trace_sessions_project", "project_id"),
        Index("idx_trace_sessions_run", "run_id"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("ui_runs.id", ondelete="CASCADE"), nullable=False)
    step_result_id = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    file_hash = Column(String(64), nullable=False, default="")
    parsed = Column(Boolean, nullable=False, default=False)
    action_count = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    browser_version = Column(String(50), nullable=True)
    parse_cache = Column(JSONColumn, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# 2. Protocol extensions (gRPC / WebSocket / SSE)
# ---------------------------------------------------------------------------


class ProtoFile(Base):
    __tablename__ = "proto_files"
    __table_args__ = (Index("idx_proto_files_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_hash = Column(String(64), nullable=False, default="")
    package_name = Column(String(200), nullable=True)
    services = Column(JSONColumn, nullable=True)
    parsed_at = Column(DateTime(timezone=True), nullable=True)
    parse_error = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ProtocolRequestConfig(Base):
    __tablename__ = "protocol_request_configs"
    __table_args__ = (UniqueConstraint("case_id", name="uq_protocol_request_config_case"),)

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("api_cases.id", ondelete="CASCADE"), nullable=False, unique=True)
    protocol = Column(String(20), nullable=False)
    grpc_proto_file_id = Column(Integer, ForeignKey("proto_files.id", ondelete="SET NULL"), nullable=True)
    grpc_service = Column(String(200), nullable=True)
    grpc_method = Column(String(200), nullable=True)
    grpc_metadata = Column(JSONColumn, nullable=True)
    grpc_request_body = Column(Text, nullable=True)
    grpc_use_reflection = Column(Boolean, nullable=False, default=False)
    grpc_deadline_ms = Column(Integer, nullable=False, default=30000)
    grpc_tls_enabled = Column(Boolean, nullable=False, default=False)
    grpc_tls_cert_path = Column(String(500), nullable=True)
    ws_url = Column(String(2000), nullable=True)
    ws_headers = Column(JSONColumn, nullable=True)
    ws_subprotocols = Column(JSONColumn, nullable=True)
    ws_connect_timeout_ms = Column(Integer, nullable=False, default=10000)
    ws_messages = Column(JSONColumn, nullable=True)
    sse_url = Column(String(2000), nullable=True)
    sse_headers = Column(JSONColumn, nullable=True)
    sse_event_types = Column(JSONColumn, nullable=True)
    sse_max_events = Column(Integer, nullable=False, default=100)
    sse_timeout_ms = Column(Integer, nullable=False, default=30000)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class WebSocketSessionLog(Base):
    __tablename__ = "ws_session_logs"
    __table_args__ = (Index("idx_ws_session_logs_history", "history_id"),)

    id = Column(Integer, primary_key=True)
    history_id = Column(Integer, nullable=False, index=True)
    direction = Column(String(10), nullable=False)
    frame_type = Column(String(10), nullable=False, default="text")
    payload_preview = Column(Text, nullable=True)
    payload_size = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# 3. Element repository + healing
# ---------------------------------------------------------------------------


class UIPage(Base):
    __tablename__ = "ui_pages"
    __table_args__ = (
        Index("idx_ui_pages_project", "project_id"),
        Index("idx_ui_pages_parent", "parent_id"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url_pattern = Column(String(500), nullable=True)
    parent_id = Column(Integer, ForeignKey("ui_pages.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    elements = relationship("UIElement", back_populates="page", cascade="all, delete-orphan")


class UIElement(Base):
    __tablename__ = "ui_elements"
    __table_args__ = (
        Index("idx_ui_elements_project", "project_id"),
        Index("idx_ui_elements_page", "page_id"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("ui_pages.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    locators = Column(JSONColumn, nullable=False, default=list)
    frame_path = Column(JSONColumn, nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    tags = Column(JSONColumn, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    heal_count = Column(Integer, nullable=False, default=0)
    is_deprecated = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    page = relationship("UIPage", back_populates="elements")


class UIStepElementRef(Base):
    __tablename__ = "ui_step_element_refs"
    __table_args__ = (
        UniqueConstraint("step_id", "element_id", name="uq_ui_step_element_ref"),
        Index("idx_ui_step_element_refs_step", "step_id"),
        Index("idx_ui_step_element_refs_element", "element_id"),
    )

    id = Column(Integer, primary_key=True)
    step_id = Column(String(36), nullable=False, index=True)
    element_id = Column(Integer, ForeignKey("ui_elements.id", ondelete="CASCADE"), nullable=False)
    override_locators = Column(JSONColumn, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class HealingRecord(Base):
    __tablename__ = "healing_records"
    __table_args__ = (
        Index("idx_healing_records_project", "project_id"),
        Index("idx_healing_records_element", "element_id"),
        Index("idx_healing_records_run", "run_id"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    element_id = Column(Integer, ForeignKey("ui_elements.id", ondelete="CASCADE"), nullable=True)
    run_id = Column(Integer, ForeignKey("ui_runs.id", ondelete="CASCADE"), nullable=True)
    step_result_id = Column(Integer, nullable=True)
    original_locator = Column(JSONColumn, nullable=False, default=dict)
    failure_reason = Column(Text, nullable=False, default="")
    page_url = Column(String(2000), nullable=True)
    dom_snapshot_path = Column(String(500), nullable=True)
    healed_locator = Column(JSONColumn, nullable=True)
    confidence = Column(Float, nullable=True)
    strategy_used = Column(String(100), nullable=True)
    candidates = Column(JSONColumn, nullable=True)
    status = Column(String(20), nullable=False, default="suggested")
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class HealingConfig(Base):
    __tablename__ = "healing_configs"
    __table_args__ = (UniqueConstraint("project_id", name="uq_healing_config_project"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)
    auto_apply_threshold = Column(Float, nullable=False, default=0.9)
    suggest_threshold = Column(Float, nullable=False, default=0.6)
    # When False (default), auto_applied only affects the current run locator —
    # shared UIElement assets are never rewritten without human review / explicit opt-in.
    auto_mutate_assets = Column(Boolean, nullable=False, default=False)
    use_llm = Column(Boolean, nullable=False, default=False)
    llm_model = Column(String(50), nullable=True)
    max_candidates = Column(Integer, nullable=False, default=5)
    capture_dom_on_failure = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# 4. Parallel execution + suite sharding
# ---------------------------------------------------------------------------


class SuiteShard(Base):
    __tablename__ = "suite_shards"
    __table_args__ = (
        UniqueConstraint("suite_execution_id", "shard_index", name="uq_suite_shard_index"),
        Index("idx_suite_shards_execution", "suite_execution_id"),
        Index("idx_suite_shards_agent", "assigned_agent_id"),
        Index("idx_suite_shards_status", "status"),
    )

    id = Column(Integer, primary_key=True)
    suite_execution_id = Column(Integer, nullable=False, index=True)
    suite_id = Column(Integer, ForeignKey("ui_suites.id", ondelete="CASCADE"), nullable=True)
    shard_index = Column(Integer, nullable=False)
    total_shards = Column(Integer, nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("desktop_agents.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    case_ids = Column(JSONColumn, nullable=False, default=list)
    total_cases = Column(Integer, nullable=False, default=0)
    completed_cases = Column(Integer, nullable=False, default=0)
    passed_cases = Column(Integer, nullable=False, default=0)
    failed_cases = Column(Integer, nullable=False, default=0)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    original_agent_id = Column(Integer, nullable=True)
    reassign_count = Column(Integer, nullable=False, default=0)


class AgentWorkerSlot(Base):
    __tablename__ = "agent_worker_slots"
    __table_args__ = (UniqueConstraint("agent_id", "slot_index", name="uq_agent_worker_slot"),)

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("desktop_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_index = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="idle")
    current_run_id = Column(Integer, ForeignKey("ui_runs.id", ondelete="SET NULL"), nullable=True)
    current_case_name = Column(String(200), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)


class ExecutionProgress(Base):
    __tablename__ = "execution_progress"
    __table_args__ = (UniqueConstraint("suite_execution_id", name="uq_execution_progress_execution"),)

    id = Column(Integer, primary_key=True)
    suite_execution_id = Column(Integer, nullable=False, unique=True)
    total_cases = Column(Integer, nullable=False, default=0)
    completed_cases = Column(Integer, nullable=False, default=0)
    passed_cases = Column(Integer, nullable=False, default=0)
    failed_cases = Column(Integer, nullable=False, default=0)
    running_cases = Column(Integer, nullable=False, default=0)
    skipped_cases = Column(Integer, nullable=False, default=0)
    estimated_remaining_ms = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseConcurrencyTag(Base):
    __tablename__ = "case_concurrency_tags"
    __table_args__ = (UniqueConstraint("project_id", "tag", name="uq_case_concurrency_tag"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    tag = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    max_concurrent = Column(Integer, nullable=False, default=1)


class CaseConcurrencyTagAssignment(Base):
    __tablename__ = "case_concurrency_tag_assignments"
    __table_args__ = (UniqueConstraint("case_id", "tag_id", name="uq_case_concurrency_assignment"),)

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("ui_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("case_concurrency_tags.id", ondelete="CASCADE"), nullable=False)


# ---------------------------------------------------------------------------
# 5. Defect integration + Flaky detection
# ---------------------------------------------------------------------------


class DefectTrackerConfig(Base):
    __tablename__ = "defect_tracker_configs"
    __table_args__ = (Index("idx_defect_tracker_configs_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    tracker_type = Column(String(20), nullable=False)
    base_url = Column(String(500), nullable=False)
    credentials_encrypted = Column(Text, nullable=False, default="")
    project_key = Column(String(100), nullable=True)
    custom_fields_mapping = Column(JSONColumn, nullable=True)
    default_issue_type = Column(String(50), nullable=True)
    default_priority = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class DefectRecord(Base):
    __tablename__ = "defect_records"
    __table_args__ = (
        Index("idx_defect_records_project", "project_id"),
        Index("idx_defect_records_status", "status"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    tracker_config_id = Column(Integer, ForeignKey("defect_tracker_configs.id", ondelete="SET NULL"), nullable=True)
    external_id = Column(String(100), nullable=True)
    external_url = Column(String(500), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="open")
    priority = Column(String(20), nullable=True)
    severity = Column(String(20), nullable=True)
    source_type = Column(String(20), nullable=False, default="manual")
    source_run_id = Column(Integer, nullable=True)
    source_step_result_id = Column(Integer, nullable=True)
    attachments = Column(JSONColumn, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    synced_at = Column(DateTime(timezone=True), nullable=True)


class DefectCaseLink(Base):
    __tablename__ = "defect_case_links"
    __table_args__ = (UniqueConstraint("defect_id", "case_type", "case_id", name="uq_defect_case_link"),)

    id = Column(Integer, primary_key=True)
    defect_id = Column(Integer, ForeignKey("defect_records.id", ondelete="CASCADE"), nullable=False, index=True)
    case_type = Column(String(10), nullable=False)
    case_id = Column(Integer, nullable=False)
    linked_at = Column(DateTime(timezone=True), default=_utcnow)
    linked_by = Column(Integer, nullable=False)


class FlakyTestRecord(Base):
    __tablename__ = "flaky_test_records"
    __table_args__ = (
        UniqueConstraint("project_id", "case_type", "case_id", name="uq_flaky_test_case"),
        Index("idx_flaky_test_records_project", "project_id"),
        Index("idx_flaky_test_records_score", "flaky_score"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    case_type = Column(String(10), nullable=False)
    case_id = Column(Integer, nullable=False)
    case_name = Column(String(200), nullable=False, default="")
    recent_results = Column(JSONColumn, nullable=False, default=list)
    total_runs = Column(Integer, nullable=False, default=0)
    pass_count = Column(Integer, nullable=False, default=0)
    fail_count = Column(Integer, nullable=False, default=0)
    status_changes = Column(Integer, nullable=False, default=0)
    flaky_score = Column(Float, nullable=False, default=0.0)
    classification = Column(String(20), nullable=False, default="stable_pass")
    is_quarantined = Column(Boolean, nullable=False, default=False)
    quarantined_at = Column(DateTime(timezone=True), nullable=True)
    quarantined_by = Column(Integer, nullable=True)
    last_status_change_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class FlakyDetectionConfig(Base):
    __tablename__ = "flaky_detection_configs"
    __table_args__ = (UniqueConstraint("project_id", name="uq_flaky_detection_config_project"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, unique=True)
    window_size = Column(Integer, nullable=False, default=20)
    flaky_high_threshold = Column(Float, nullable=False, default=0.4)
    flaky_low_threshold = Column(Float, nullable=False, default=0.15)
    auto_quarantine = Column(Boolean, nullable=False, default=False)
    auto_quarantine_score = Column(Float, nullable=False, default=0.6)
    alert_on_new_flaky = Column(Boolean, nullable=False, default=True)
    notification_channel_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# 6. Network interception
# ---------------------------------------------------------------------------


class UINetworkRule(Base):
    __tablename__ = "ui_network_rules"
    __table_args__ = (Index("idx_ui_network_rules_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url_pattern = Column(String(1000), nullable=False)
    pattern_type = Column(String(10), nullable=False, default="glob")
    method_filter = Column(String(20), nullable=True)
    resource_type = Column(String(30), nullable=True)
    action = Column(String(20), nullable=False, default="fulfill")
    fulfill_status = Column(Integer, nullable=True)
    fulfill_headers = Column(JSONColumn, nullable=True)
    fulfill_body = Column(Text, nullable=True)
    fulfill_content_type = Column(String(100), nullable=True)
    modify_headers = Column(JSONColumn, nullable=True)
    modify_body_jsonpath = Column(JSONColumn, nullable=True)
    delay_ms = Column(Integer, nullable=True)
    abort_reason = Column(String(50), nullable=True)
    source = Column(String(20), nullable=False, default="manual")
    mock_rule_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class UINetworkRuleAssignment(Base):
    __tablename__ = "ui_network_rule_assignments"
    __table_args__ = (UniqueConstraint("rule_id", "target_type", "target_id", name="uq_ui_network_rule_assignment"),)

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("ui_network_rules.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(10), nullable=False)
    target_id = Column(Integer, nullable=False)
    priority = Column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# 7. API contract / health / codegen support tables
# ---------------------------------------------------------------------------


class OpenAPISnapshot(Base):
    __tablename__ = "openapi_snapshots"
    __table_args__ = (Index("idx_openapi_snapshots_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    group_id = Column(Integer, nullable=True)
    source_url = Column(String(1000), nullable=True)
    source_type = Column(String(20), nullable=False, default="upload")
    spec_version = Column(String(50), nullable=True)
    content_hash = Column(String(64), nullable=False, default="")
    spec_content = Column(Text, nullable=False)
    parsed_endpoints = Column(JSONColumn, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class SchemaChangeRecord(Base):
    __tablename__ = "schema_change_records"
    __table_args__ = (Index("idx_schema_change_records_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    old_snapshot_id = Column(Integer, ForeignKey("openapi_snapshots.id", ondelete="CASCADE"), nullable=False)
    new_snapshot_id = Column(Integer, ForeignKey("openapi_snapshots.id", ondelete="CASCADE"), nullable=False)
    changes = Column(JSONColumn, nullable=False, default=list)
    breaking_changes = Column(JSONColumn, nullable=False, default=list)
    is_breaking = Column(Boolean, nullable=False, default=False)
    notified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class APIContractRule(Base):
    __tablename__ = "api_contract_rules"
    __table_args__ = (Index("idx_api_contract_rules_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    case_id = Column(Integer, nullable=False)
    snapshot_id = Column(Integer, ForeignKey("openapi_snapshots.id", ondelete="CASCADE"), nullable=False)
    endpoint_path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    validate_request = Column(Boolean, nullable=False, default=True)
    validate_response = Column(Boolean, nullable=False, default=True)
    strict_mode = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class APIHealthMonitor(Base):
    __tablename__ = "api_health_monitors"
    __table_args__ = (Index("idx_api_health_monitors_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    case_id = Column(Integer, nullable=False)
    environment_id = Column(Integer, nullable=False)
    interval_seconds = Column(Integer, nullable=False, default=300)
    timeout_ms = Column(Integer, nullable=False, default=10000)
    expected_status = Column(Integer, nullable=False, default=200)
    max_response_time_ms = Column(Integer, nullable=True)
    alert_consecutive_failures = Column(Integer, nullable=False, default=3)
    alert_response_time_degradation = Column(Float, nullable=True)
    notification_channel_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_check_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class APIHealthCheckResult(Base):
    __tablename__ = "api_health_check_results"
    __table_args__ = (
        Index("idx_api_health_check_results_monitor", "monitor_id"),
        Index("idx_api_health_check_results_checked", "checked_at"),
    )

    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey("api_health_monitors.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(10), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), default=_utcnow, index=True)


# ---------------------------------------------------------------------------
# 8. Flow graph + review + requirements + reports
# ---------------------------------------------------------------------------


class ScenarioFlowGraph(Base):
    __tablename__ = "scenario_flow_graphs"
    __table_args__ = (UniqueConstraint("scenario_id", name="uq_scenario_flow_graph"),)

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, nullable=False, unique=True)
    nodes = Column(JSONColumn, nullable=False, default=list)
    edges = Column(JSONColumn, nullable=False, default=list)
    viewport = Column(JSONColumn, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseReview(Base):
    __tablename__ = "case_reviews"
    __table_args__ = (
        Index("idx_case_reviews_project", "project_id"),
        Index("idx_case_reviews_state", "state"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    case_type = Column(String(10), nullable=False)
    case_id = Column(Integer, nullable=False)
    case_version = Column(Integer, nullable=True)
    state = Column(String(20), nullable=False, default="draft")
    submitted_by = Column(Integer, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    required_approvals = Column(Integer, nullable=False, default=1)
    current_approvals = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseReviewComment(Base):
    __tablename__ = "case_review_comments"
    __table_args__ = (Index("idx_case_review_comments_review", "review_id"),)

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("case_reviews.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    step_id = Column(String(36), nullable=True)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class CaseReviewAction(Base):
    __tablename__ = "case_review_actions"
    __table_args__ = (Index("idx_case_review_actions_review", "review_id"),)

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("case_reviews.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Requirement(Base):
    __tablename__ = "requirements"
    __table_args__ = (Index("idx_requirements_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    external_id = Column(String(100), nullable=True)
    external_url = Column(String(500), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), nullable=True)
    status = Column(String(30), nullable=False, default="open")
    sprint = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class RequirementCaseLink(Base):
    __tablename__ = "requirement_case_links"
    __table_args__ = (UniqueConstraint("requirement_id", "case_type", "case_id", name="uq_requirement_case_link"),)

    id = Column(Integer, primary_key=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    case_type = Column(String(10), nullable=False)
    case_id = Column(Integer, nullable=False)
    coverage_type = Column(String(20), nullable=False, default="functional")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class ReportTemplate(Base):
    __tablename__ = "report_templates"
    __table_args__ = (Index("idx_report_templates_project", "project_id"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    logo_path = Column(String(500), nullable=True)
    primary_color = Column(String(20), nullable=False, default="#409EFF")
    company_name = Column(String(200), nullable=True)
    footer_text = Column(String(500), nullable=True)
    sections = Column(JSONColumn, nullable=False, default=list)
    custom_fields = Column(JSONColumn, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
