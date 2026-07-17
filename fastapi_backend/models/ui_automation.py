"""UI Automation data models."""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON, TypeDecorator

from fastapi_backend.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _gen_uuid_str() -> str:
    return str(_uuid.uuid4())


class JSONColumn(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class UICase(Base):
    __tablename__ = 'ui_cases'
    __table_args__ = (
        Index('idx_ui_cases_user_id', 'user_id'),
        Index('idx_ui_cases_project_id', 'project_id'),
        Index('idx_ui_cases_group_id', 'group_id'),
        Index('idx_ui_cases_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    group_id = Column(Integer, ForeignKey('ui_case_groups.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=False, index=True)
    owner_id = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default='draft')
    priority = Column(String(20), nullable=False, default='medium')
    tags = Column(JSONColumn, nullable=True, default=list)
    base_url = Column(Text, nullable=True)
    default_timeout_ms = Column(Integer, nullable=False, default=10000)
    navigation_timeout_ms = Column(Integer, nullable=False, default=30000)
    viewport = Column(JSONColumn, nullable=True)
    locale = Column(String(20), nullable=True)
    timezone_id = Column(String(50), nullable=True)
    color_scheme = Column(String(20), nullable=True)
    storage_state_ref = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    current_version_id = Column(Integer, ForeignKey('ui_case_versions.id', ondelete='SET NULL', use_alter=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    versions = relationship(
        'UICaseVersion',
        back_populates='case',
        foreign_keys='UICaseVersion.case_id',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    group = relationship('UICaseGroup', back_populates='cases')
    current_version = relationship('UICaseVersion', foreign_keys=[current_version_id], post_update=True)


class UICaseVersion(Base):
    __tablename__ = 'ui_case_versions'
    __table_args__ = (
        Index('idx_ui_case_versions_case_id', 'case_id'),
        UniqueConstraint('case_id', 'version_number', name='uq_ui_case_version_number'),
    )

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('ui_cases.id', ondelete='CASCADE'), nullable=False)
    version_number = Column(Integer, nullable=False)
    snapshot_json = Column(JSONColumn, nullable=False)
    change_summary = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    is_current = Column(Boolean, nullable=False, default=False)

    case = relationship('UICase', back_populates='versions', foreign_keys=[case_id])


class UIStep(Base):
    __tablename__ = 'ui_steps'
    __table_args__ = (
        Index('idx_ui_steps_case_id', 'case_id'),
        Index('idx_ui_steps_order', 'case_id', 'order'),
    )

    id = Column(String(36), primary_key=True, default=_gen_uuid_str)
    case_id = Column(Integer, ForeignKey('ui_cases.id', ondelete='CASCADE'), nullable=False)
    order = Column(Integer, nullable=False, default=10)
    name = Column(String(200), nullable=True)
    type = Column(String(40), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    breakpoint = Column(Boolean, nullable=False, default=False)
    locator = Column(JSONColumn, nullable=True)
    input = Column(JSONColumn, nullable=True)
    timeout_ms = Column(Integer, nullable=True)
    retry = Column(JSONColumn, nullable=True)
    continue_on_failure = Column(Boolean, nullable=False, default=False)
    screenshot = Column(String(20), nullable=True, default='on-failure')
    condition = Column(Text, nullable=True)
    children = Column(JSONColumn, nullable=True, default=list)


class UICaseGroup(Base):
    __tablename__ = 'ui_case_groups'
    __table_args__ = (
        Index('idx_ui_case_groups_parent_id', 'parent_id'),
        Index('idx_ui_case_groups_user_id', 'user_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey('ui_case_groups.id', ondelete='SET NULL'), nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    parent = relationship('UICaseGroup', remote_side='UICaseGroup.id', backref='children')
    cases = relationship('UICase', back_populates='group', passive_deletes=True)


class UISuite(Base):
    __tablename__ = 'ui_suites'
    __table_args__ = (
        Index('idx_ui_suites_user_id', 'user_id'),
        Index('idx_ui_suites_project_id', 'project_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=False)
    stop_on_first_failure = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    items = relationship('UISuiteItem', back_populates='suite', cascade='all, delete-orphan', passive_deletes=True, order_by='UISuiteItem.order')


class UISuiteItem(Base):
    __tablename__ = 'ui_suite_items'
    __table_args__ = (Index('idx_ui_suite_items_suite_id', 'suite_id'),)

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey('ui_suites.id', ondelete='CASCADE'), nullable=False)
    case_id = Column(Integer, ForeignKey('ui_cases.id', ondelete='CASCADE'), nullable=False)
    pinned_version_id = Column(Integer, ForeignKey('ui_case_versions.id', ondelete='SET NULL', use_alter=True), nullable=True)
    order = Column(Integer, nullable=False, default=10)
    enabled = Column(Boolean, nullable=False, default=True)
    data_source = Column(JSONColumn, nullable=True)
    overrides = Column(JSONColumn, nullable=True)

    suite = relationship('UISuite', back_populates='items')


class UIRun(Base):
    __tablename__ = 'ui_runs'
    __table_args__ = (
        Index('idx_ui_runs_run_key', 'run_key', unique=True),
        Index('idx_ui_runs_user_id', 'user_id'),
        Index('idx_ui_runs_project_id', 'project_id'),
        Index('idx_ui_runs_status', 'status'),
        Index('idx_ui_runs_agent_id', 'agent_id'),
        Index('idx_ui_runs_user_client_run_key', 'user_id', 'client_run_key', unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    run_key = Column(String(36), nullable=False, default=_gen_uuid_str)
    project_id = Column(Integer, nullable=True)
    case_id = Column(Integer, ForeignKey('ui_cases.id', ondelete='SET NULL'), nullable=True)
    case_version_id = Column(Integer, ForeignKey('ui_case_versions.id', ondelete='SET NULL', use_alter=True), nullable=True)
    suite_id = Column(Integer, ForeignKey('ui_suites.id', ondelete='SET NULL'), nullable=True)
    agent_id = Column(Integer, ForeignKey('desktop_agents.id', ondelete='SET NULL'), nullable=True)
    client_run_key = Column(String(64), nullable=True)
    trigger_type = Column(String(20), nullable=False, default='manual')
    triggered_by = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default='queued')
    queued_at = Column(DateTime(timezone=True), default=_utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    browser = Column(String(20), nullable=True)
    browser_version = Column(String(50), nullable=True)
    desktop_version = Column(String(50), nullable=True)
    engine_version = Column(String(50), nullable=True)
    environment_id = Column(Integer, nullable=True)
    dataset_iteration = Column(Integer, nullable=True)
    retry_of_run_id = Column(Integer, ForeignKey('ui_runs.id', ondelete='SET NULL'), nullable=True)
    total_steps = Column(Integer, nullable=False, default=0)
    passed_steps = Column(Integer, nullable=False, default=0)
    failed_steps = Column(Integer, nullable=False, default=0)
    skipped_steps = Column(Integer, nullable=False, default=0)
    error_code = Column(String(50), nullable=True)
    error_summary = Column(Text, nullable=True)
    artifact_manifest = Column(JSONColumn, nullable=True)
    user_id = Column(Integer, nullable=False)

    step_results = relationship('UIStepResult', back_populates='run', cascade='all, delete-orphan', passive_deletes=True)


class UIStepResult(Base):
    __tablename__ = 'ui_step_results'
    __table_args__ = (
        Index('idx_ui_step_results_run_id', 'run_id'),
        Index('idx_ui_step_results_step_id', 'step_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey('ui_runs.id', ondelete='CASCADE'), nullable=False)
    step_id = Column(String(36), nullable=False)
    iteration = Column(Integer, nullable=False, default=0)
    attempt = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default='pending')
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    resolved_locator = Column(Text, nullable=True)
    input_preview = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    screenshot_artifact_id = Column(Integer, nullable=True)
    trace_event_ref = Column(String(200), nullable=True)

    run = relationship('UIRun', back_populates='step_results')


class DesktopAgent(Base):
    __tablename__ = 'desktop_agents'
    __table_args__ = (
        Index('idx_desktop_agents_agent_key', 'agent_key', unique=True),
        Index('idx_desktop_agents_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_key = Column(String(36), nullable=False, default=_gen_uuid_str)
    name = Column(String(200), nullable=False)
    owner_id = Column(Integer, nullable=False)
    team_id = Column(Integer, nullable=True)
    hostname = Column(String(200), nullable=True)
    os_version = Column(String(100), nullable=True)
    desktop_version = Column(String(50), nullable=True)
    capabilities = Column(JSONColumn, nullable=True, default=dict)
    status = Column(String(20), nullable=False, default='offline')
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    max_parallel = Column(Integer, nullable=False, default=1)
    current_runs = Column(Integer, nullable=False, default=0)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class UIArtifact(Base):
    __tablename__ = 'ui_artifacts'
    __table_args__ = (
        Index('idx_ui_artifacts_run_id', 'run_id'),
        Index('idx_ui_artifacts_type', 'type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey('ui_runs.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(30), nullable=False)
    filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    storage_path = Column(Text, nullable=False)
    storage_type = Column(String(20), nullable=False, default='local')
    created_at = Column(DateTime(timezone=True), default=_utcnow)

