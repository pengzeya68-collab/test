"""Regression coverage for advisory failure attribution of suite executions."""

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import AutomationExecution, AutomationExecutionItem
from fastapi_backend.models.ui_automation import AIAnalysisRecord


@pytest.fixture(autouse=True)
def suite_ai_admin():
    async def _admin():
        return SimpleNamespace(
            id=1, username="suite-ai-admin", is_active=True, is_admin=True, is_super_admin=True, role_id=None
        )

    app.dependency_overrides[get_current_user] = _admin
    yield
    app.dependency_overrides.pop(get_current_user, None)


async def _make_execution(db_session, *, status="failed", error_message=None, error_code=None, items=()):
    execution = AutomationExecution(
        execution_type="suite",
        target_type="suite",
        target_id=99,
        user_id=1,
        status=status,
        attempt=1,
        idempotency_key=f"test-{uuid.uuid4().hex}",
        error_code=error_code,
        error_message=error_message,
    )
    db_session.add(execution)
    await db_session.flush()
    for sequence, item_error in enumerate(items, start=1):
        db_session.add(
            AutomationExecutionItem(
                execution_id=execution.id,
                sequence=sequence,
                target_type="scenario",
                target_id=sequence,
                target_name=f"场景{sequence}",
                status="failed",
                error_message=item_error,
            )
        )
    await db_session.commit()
    await db_session.refresh(execution)
    return execution


def _analyze(client, execution) -> dict:
    response = client.post(f"/api/auto-test/suites/executions/{execution.public_id}/ai/failure-analysis")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_execution_failure_analysis_is_advisory_and_audited(client, db_session):
    execution = await _make_execution(
        db_session,
        error_message="runner heartbeat lost before completion",
        items=["GET /orders failed: connection refused by 10.0.0.8:8080"],
    )
    payload = _analyze(client, execution)
    assert payload["category"] == "environment"
    assert payload["advisory_only"] is True
    assert payload["engine"] == "guarded-heuristic-v1"
    assert payload["evidence"] and payload["unknowns"] and payload["next_actions"]
    assert any("场景1" in line for line in payload["evidence"])

    record = await db_session.scalar(select(AIAnalysisRecord).where(AIAnalysisRecord.id == payload["analysis_id"]))
    assert record is not None
    assert record.analysis_type == "failure_attribution"
    assert record.target_type == "automation_execution"
    assert record.target_id == execution.id
    # The execution must not be mutated by an advisory analysis.
    await db_session.refresh(execution)
    assert execution.status == "failed"


@pytest.mark.asyncio
async def test_execution_failure_analysis_covers_all_categories(client, db_session):
    data_run = await _make_execution(
        db_session, items=["POST /accounts failed: duplicate key value violates unique constraint"]
    )
    assert _analyze(client, data_run)["category"] == "data"

    product_run = await _make_execution(
        db_session, items=["POST /orders failed: status 500 internal server error from order service"]
    )
    assert _analyze(client, product_run)["category"] == "product_defect"

    script_run = await _make_execution(
        db_session, items=["step 2 failed: jsonpath extractor $.data.token matched nothing"]
    )
    assert _analyze(client, script_run)["category"] == "script"

    assertion_run = await _make_execution(db_session, items=["assert failed: expected 200 but got 409, value mismatch"])
    result = _analyze(client, assertion_run)
    assert result["category"] == "product_defect"
    assert result["confidence"] < 0.7

    unknown_run = await _make_execution(db_session, items=["step aborted for an unrecorded reason"])
    assert _analyze(client, unknown_run)["category"] == "unknown"


@pytest.mark.asyncio
async def test_execution_failure_analysis_redacts_sensitive_error_text(client, db_session):
    execution = await _make_execution(
        db_session,
        items=["POST /login failed: password=hunter2secret rejected and bearer abcdef1234567890.xyz expired"],
    )
    payload = _analyze(client, execution)
    joined = " ".join(payload["evidence"])
    assert "hunter2secret" not in joined
    assert "abcdef1234567890" not in joined
    assert "[REDACTED]" in joined

    record = await db_session.scalar(select(AIAnalysisRecord).where(AIAnalysisRecord.id == payload["analysis_id"]))
    stored = str(record.input_redacted) + str(record.output)
    assert "hunter2secret" not in stored


@pytest.mark.asyncio
async def test_execution_failure_analysis_requires_terminal_failure(client, db_session):
    running = await _make_execution(db_session, status="running")
    response = client.post(f"/api/auto-test/suites/executions/{running.public_id}/ai/failure-analysis")
    assert response.status_code == 409

    passed = await _make_execution(db_session, status="passed")
    response = client.post(f"/api/auto-test/suites/executions/{passed.public_id}/ai/failure-analysis")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_execution_failure_analysis_is_user_scoped(client, db_session):
    execution = AutomationExecution(
        execution_type="suite",
        target_type="suite",
        target_id=99,
        user_id=2,
        status="failed",
        attempt=1,
        idempotency_key=f"test-{uuid.uuid4().hex}",
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)
    response = client.post(f"/api/auto-test/suites/executions/{execution.public_id}/ai/failure-analysis")
    assert response.status_code == 404
