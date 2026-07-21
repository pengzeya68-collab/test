"""
Pydantic schemas for the UI Automation module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


STEP_TYPES = [
    "goto",
    "reload",
    "go_back",
    "switch_page",
    "close_page",
    "set_viewport",
    "click",
    "double_click",
    "fill",
    "type",
    "clear",
    "press",
    "check",
    "uncheck",
    "select_option",
    "hover",
    "focus",
    "scroll_into_view",
    "drag_and_drop",
    "upload_file",
    "download",
    "accept_dialog",
    "dismiss_dialog",
    "wait_for_element",
    "wait_for_url",
    "wait_for_load_state",
    "wait_for_timeout",
    "assert_visible",
    "assert_hidden",
    "assert_enabled",
    "assert_disabled",
    "assert_editable",
    "assert_checked",
    "assert_text_equals",
    "assert_text_contains",
    "assert_text_matches",
    "assert_value",
    "assert_attribute",
    "assert_css_property",
    "assert_element_count",
    "assert_url",
    "assert_title",
    "set_variable",
    "extract_text",
    "extract_value",
    "extract_attribute",
    "extract_url",
]

TERMINAL_RUN_STATUSES = {"passed", "failed", "cancelled", "timed_out", "infra_error"}
RUN_STATUSES = [
    "queued",
    "waiting_for_agent",
    "assigned",
    "starting",
    "running",
    "cancel_requested",
    "passed",
    "failed",
    "cancelled",
    "timed_out",
    "infra_error",
]
ARTIFACT_TYPES = ["screenshot", "video", "trace", "console_log", "network", "download", "html_report"]


class AppBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LocatorSchema(AppBaseModel):
    strategy: Literal["test_id", "role", "label", "placeholder", "text", "css", "xpath"]
    value: str = Field(..., min_length=1, max_length=2000)
    options: dict[str, Any] = Field(default_factory=dict)
    fallbacks: list["LocatorSchema"] = Field(default_factory=list)
    frame_path: list[str] = Field(default_factory=list, alias="framePath")


class RetryConfig(AppBaseModel):
    count: int = Field(default=0, ge=0, le=10)
    delay_ms: int = Field(default=0, ge=0, le=60000)


class StepSnapshot(AppBaseModel):
    id: str
    order: int = Field(..., ge=0)
    name: Optional[str] = None
    type: str
    enabled: bool = True
    breakpoint: bool = False
    locator: Optional[LocatorSchema] = None
    input: Optional[Any] = None
    timeout_ms: Optional[int] = Field(None, ge=100, le=120000)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    continue_on_failure: bool = False
    screenshot: Literal["always", "on-failure", "never"] = "on-failure"
    condition: Optional[str] = None
    children: list["StepSnapshot"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_step_type(self) -> "StepSnapshot":
        if self.type not in STEP_TYPES:
            raise ValueError(f"Unsupported step type: {self.type}")
        return self


class UICaseGroupCreate(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0


class UICaseGroupUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class UICaseGroupOut(AppBaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UICaseCreate(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    group_id: Optional[int] = None
    project_id: Optional[int] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    tags: list[str] = Field(default_factory=list)
    base_url: Optional[str] = None
    default_timeout_ms: int = Field(10000, ge=1000, le=120000)
    navigation_timeout_ms: int = Field(30000, ge=1000, le=120000)
    viewport: Optional[dict[str, int]] = None
    locale: Optional[str] = None
    timezone_id: Optional[str] = None
    color_scheme: Optional[Literal["light", "dark", "no-preference"]] = None


class UICaseUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    group_id: Optional[int] = None
    status: Optional[Literal["draft", "active", "deprecated", "archived"]] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    tags: Optional[list[str]] = None
    base_url: Optional[str] = None
    default_timeout_ms: Optional[int] = Field(None, ge=1000, le=120000)
    navigation_timeout_ms: Optional[int] = Field(None, ge=1000, le=120000)
    viewport: Optional[dict[str, int]] = None
    locale: Optional[str] = None
    timezone_id: Optional[str] = None
    color_scheme: Optional[Literal["light", "dark", "no-preference"]] = None
    is_active: Optional[bool] = None


class UICaseOut(AppBaseModel):
    id: int
    project_id: Optional[int] = None
    group_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    user_id: int
    owner_id: Optional[int] = None
    status: str
    priority: str
    tags: Optional[list[str]] = None
    base_url: Optional[str] = None
    default_timeout_ms: int
    navigation_timeout_ms: int
    viewport: Optional[dict[str, Any]] = None
    locale: Optional[str] = None
    timezone_id: Optional[str] = None
    color_scheme: Optional[str] = None
    storage_state_ref: Optional[str] = None
    is_active: bool
    current_version_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UICaseWithStepsOut(UICaseOut):
    steps: list[StepSnapshot] = Field(default_factory=list)


class UICaseVersionCreate(AppBaseModel):
    change_summary: Optional[str] = None


class UICaseVersionOut(AppBaseModel):
    id: int
    case_id: int
    version_number: int
    snapshot_json: dict[str, Any]
    change_summary: Optional[str] = None
    created_by: int
    created_at: Optional[datetime] = None
    is_current: bool


class UISuiteItemCreate(AppBaseModel):
    case_id: int
    pinned_version_id: Optional[int] = None
    order: int = 10
    enabled: bool = True
    data_source: Optional[dict[str, Any]] = None
    overrides: Optional[dict[str, Any]] = None


class UISuiteItemOut(AppBaseModel):
    id: int
    suite_id: int
    case_id: int
    pinned_version_id: Optional[int] = None
    order: int
    enabled: bool
    data_source: Optional[dict[str, Any]] = None
    overrides: Optional[dict[str, Any]] = None


class UISuiteCreate(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: Optional[int] = None
    stop_on_first_failure: bool = False


class UISuiteUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: Optional[int] = None
    stop_on_first_failure: Optional[bool] = None
    is_active: Optional[bool] = None


class UISuiteOut(AppBaseModel):
    id: int
    project_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    user_id: int
    stop_on_first_failure: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[UISuiteItemOut] = Field(default_factory=list)


class UIStepSave(AppBaseModel):
    id: Optional[str] = None
    order: int = Field(10, ge=0)
    name: Optional[str] = None
    type: str
    enabled: bool = True
    breakpoint: bool = False
    locator: Optional[LocatorSchema] = None
    input: Optional[Any] = None
    timeout_ms: Optional[int] = Field(None, ge=100, le=120000)
    retry: Optional[RetryConfig] = None
    continue_on_failure: bool = False
    screenshot: Literal["always", "on-failure", "never"] = "on-failure"
    condition: Optional[str] = None
    children: Optional[list[Any]] = None

    @model_validator(mode="after")
    def validate_step_type(self) -> "UIStepSave":
        if self.type not in STEP_TYPES:
            raise ValueError(f"Unsupported step type: {self.type}")
        return self


class UIStepBatchSave(AppBaseModel):
    steps: list[UIStepSave] = Field(default_factory=list)


class UIRunCreate(AppBaseModel):
    case_id: Optional[int] = None
    suite_id: Optional[int] = None
    case_version_id: Optional[int] = None
    environment_id: Optional[int] = None
    agent_id: Optional[int] = None
    client_run_key: Optional[str] = Field(None, min_length=8, max_length=64)
    trigger_type: Literal["manual", "scheduled", "ci", "api"] = "manual"

    @model_validator(mode="after")
    def validate_target(self) -> "UIRunCreate":
        if bool(self.case_id) == bool(self.suite_id):
            raise ValueError("Exactly one of case_id or suite_id is required")
        return self


class UIRunOut(AppBaseModel):
    id: int
    run_key: str
    project_id: Optional[int] = None
    case_id: Optional[int] = None
    case_version_id: Optional[int] = None
    suite_id: Optional[int] = None
    agent_id: Optional[int] = None
    client_run_key: Optional[str] = None
    trigger_type: str
    triggered_by: Optional[int] = None
    status: str
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    desktop_version: Optional[str] = None
    engine_version: Optional[str] = None
    environment_id: Optional[int] = None
    dataset_iteration: Optional[int] = None
    retry_of_run_id: Optional[int] = None
    automation_execution_id: Optional[int] = None
    execution_id: Optional[str] = None
    attempt: int = 1
    last_heartbeat_at: Optional[datetime] = None
    lease_expires_at: Optional[datetime] = None
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    error_code: Optional[str] = None
    error_summary: Optional[str] = None
    artifact_manifest: Optional[dict[str, Any]] = None


class UIStepResultOut(AppBaseModel):
    id: int
    run_id: int
    step_id: str
    iteration: int
    attempt: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    resolved_locator: Optional[str] = None
    input_preview: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_artifact_id: Optional[int] = None
    trace_event_ref: Optional[str] = None


class UIRunEventIn(AppBaseModel):
    sequence: int = Field(..., ge=1)
    type: str
    stepId: Optional[str] = None
    stepName: Optional[str] = None
    stepType: Optional[str] = None
    durationMs: Optional[int] = Field(None, ge=0)
    totalSteps: Optional[int] = Field(None, ge=0)
    passedSteps: Optional[int] = Field(None, ge=0)
    failedSteps: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    reason: Optional[str] = None
    error: Optional[str] = None
    screenshotPath: Optional[str] = None
    level: Optional[str] = None
    message: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    httpStatus: Optional[int] = Field(None, ge=0, le=599)
    occurred_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_step_event(self) -> "UIRunEventIn":
        if self.type.startswith("step:") and not self.stepId:
            raise ValueError("stepId is required for step events")
        return self


class UIRunEventBatchIn(AppBaseModel):
    events: list[UIRunEventIn] = Field(default_factory=list, max_length=1000)


class UIRunEventBatchOut(AppBaseModel):
    accepted: int
    ignored: int
    last_sequence: int
    status: str


class UIArtifactCreate(AppBaseModel):
    type: Literal["screenshot", "video", "trace", "console_log", "network", "download", "html_report"]
    filename: str = Field(..., min_length=1, max_length=500)
    mime_type: Optional[str] = Field(None, max_length=100)
    size_bytes: Optional[int] = Field(None, ge=0)


class UIArtifactLinkIn(AppBaseModel):
    artifact_manifest_id: int = Field(..., ge=1)


class UIArtifactOut(AppBaseModel):
    id: int
    run_id: int
    type: str
    filename: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    storage_path: str
    storage_type: str
    artifact_manifest_id: Optional[int] = None
    created_at: Optional[datetime] = None


class DesktopAgentRegister(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    hostname: Optional[str] = None
    os_version: Optional[str] = None
    desktop_version: Optional[str] = None
    capabilities: Optional[dict[str, Any]] = None
    max_parallel: int = Field(1, ge=1, le=20)


class DesktopAgentOut(AppBaseModel):
    id: int
    agent_key: str
    name: str
    owner_id: int
    team_id: Optional[int] = None
    hostname: Optional[str] = None
    os_version: Optional[str] = None
    desktop_version: Optional[str] = None
    capabilities: Optional[dict[str, Any]] = None
    status: str
    last_heartbeat_at: Optional[datetime] = None
    max_parallel: int
    current_runs: int
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AIAnalysisFeedbackIn(AppBaseModel):
    accepted: bool
    corrected_category: Optional[Literal["environment", "data", "product_defect", "script", "unknown"]] = None
    comment: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_correction(self) -> "AIAnalysisFeedbackIn":
        if self.accepted and self.corrected_category is not None:
            raise ValueError("accepted feedback cannot include corrected_category")
        if not self.accepted and self.corrected_category is None:
            raise ValueError("corrected_category is required when accepted is false")
        return self


LocatorSchema.model_rebuild()
StepSnapshot.model_rebuild()
UIStepSave.model_rebuild()
