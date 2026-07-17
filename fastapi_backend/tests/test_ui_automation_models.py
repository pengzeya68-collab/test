"""
Unit tests for UI automation models and schemas.

Phase 0 gate: verify that the new models can be imported, have correct
table names, and the Pydantic schemas validate properly.
"""

import pytest


def test_models_importable():
    """Models module imports without error and all expected classes exist."""
    from fastapi_backend.models.ui_automation import (
        UICase,
        UICaseGroup,
        UICaseVersion,
        UIStep,
        UISuite,
        UISuiteItem,
        UIRun,
        UIStepResult,
        DesktopAgent,
        UIArtifact,
    )

    assert UICase.__tablename__ == "ui_cases"
    assert UICaseGroup.__tablename__ == "ui_case_groups"
    assert UICaseVersion.__tablename__ == "ui_case_versions"
    assert UIStep.__tablename__ == "ui_steps"
    assert UISuite.__tablename__ == "ui_suites"
    assert UISuiteItem.__tablename__ == "ui_suite_items"
    assert UIRun.__tablename__ == "ui_runs"
    assert UIStepResult.__tablename__ == "ui_step_results"
    assert DesktopAgent.__tablename__ == "desktop_agents"
    assert UIArtifact.__tablename__ == "ui_artifacts"


def test_schemas_validation():
    """Pydantic schemas validate input correctly."""
    from fastapi_backend.schemas.ui_automation import (
        UICaseCreate,
        UICaseGroupCreate,
        LocatorSchema,
        StepSnapshot,
        RetryConfig,
    )

    # Valid case
    case = UICaseCreate(name="Test Login Flow", base_url="https://example.com")
    assert case.name == "Test Login Flow"
    assert case.default_timeout_ms == 10000

    # Valid locator
    loc = LocatorSchema(strategy="role", value="button", options={"name": "Login"})
    assert loc.strategy == "role"
    assert loc.fallbacks == []

    # Valid step snapshot
    step = StepSnapshot(
        id="abc-123",
        order=10,
        type="click",
        locator=loc,
        retry=RetryConfig(),
    )
    assert step.type == "click"
    assert step.retry.count == 0

    # Invalid: empty name
    with pytest.raises(Exception):
        UICaseCreate(name="")

    # Invalid: name too long
    with pytest.raises(Exception):
        UICaseCreate(name="x" * 201)


def test_feature_flag_config():
    """UI_AUTOMATION_ENABLED is present in settings."""
    from fastapi_backend.core.config import settings

    assert hasattr(settings, "UI_AUTOMATION_ENABLED")
    assert isinstance(settings.UI_AUTOMATION_ENABLED, bool)


def test_router_importable():
    """Router module imports and exposes a router with correct prefix."""
    from fastapi_backend.routers.ui_automation import router

    assert router.prefix == "/api/ui-automation"
    assert len(router.routes) > 0

    # Check key routes exist
    route_paths = {r.path for r in router.routes}
    assert "/api/ui-automation/cases" in route_paths
    assert "/api/ui-automation/cases/{case_id}" in route_paths
    assert "/api/ui-automation/cases/{case_id}/versions" in route_paths
    assert "/api/ui-automation/groups" in route_paths
    assert "/api/ui-automation/health" in route_paths


def test_router_registered():
    """Router is registered in the router registry."""
    from fastapi_backend.core.router_registry import _ROUTER_MODULES

    assert "ui_automation" in _ROUTER_MODULES
    assert "fastapi_backend.routers.ui_automation" in _ROUTER_MODULES["ui_automation"]
