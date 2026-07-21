"""Regression coverage for execution resilience, artifacts and Mock faults."""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from fastapi_backend.models.autotest import (
    ArtifactManifest,
    ArtifactUploadSession,
    AutomationExecution,
    AutomationExecutionItem,
    ExecutionEvent,
    MockRequestLog,
    MockProject,
    AutoTestScenario,
    AutoTestScenarioStep,
    TestSuite as SuiteModel,
    TestSuiteScenario as SuiteScenarioModel,
    TestSuiteSchedule as SuiteScheduleModel,
    ImportJob,
)
from fastapi_backend.models.ui_automation import DesktopAgent, UIRun
from fastapi_backend.services import suite_execution_service
from fastapi_backend.services import suite_schedule_service
from fastapi_backend.routers import autotest_suites as autotest_suites_router
from fastapi_backend.services.ui_automation import agent_service, run_service
from fastapi_backend.services.artifact_maintenance import cleanup_expired_artifacts
from fastapi_backend.services.capture_import import normalize_captured_exchange
from fastapi_backend.services.mock_service import mock_engine
from fastapi_backend.routers.mock_api import _validate_fault_config
from fastapi_backend.tests.test_autotest_compat import autotest_client, autotest_engine, autotest_session_factory


def _rule(**overrides):
    values = {
        "id": 17,
        "delay_ms": 0,
        "fault_type": None,
        "fault_config": {},
        "response_status": 201,
        "response_headers": {"X-Base": "true"},
        "response_body": {"ok": True},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_capture_normalization_redacts_page_url_query_credentials():
    captured = normalize_captured_exchange(
        {
            "method": "GET",
            "url": "https://api.example.test/orders?token=api-secret",
            "pageUrl": "https://shop.example.test/checkout?access_token=page-secret&tab=confirm",
            "resourceType": "fetch",
            "status": 200,
        }
    )
    assert "api-secret" not in captured["url"]
    assert captured["page_url"] == "https://shop.example.test/checkout?access_token={{ACCESS_TOKEN}}&tab=confirm"


@pytest.mark.asyncio
async def test_legacy_suite_json_is_backed_up_and_cut_over_once(autotest_session_factory, tmp_path, monkeypatch):
    legacy_file = tmp_path / "suites.json"
    legacy_runs_file = tmp_path / "runs" / "runs.json"
    legacy_runs_file.parent.mkdir()
    monkeypatch.setattr(autotest_suites_router, "_LEGACY_SUITES_FILE", legacy_file)
    monkeypatch.setattr(autotest_suites_router, "_LEGACY_RUNS_FILE", legacy_runs_file)

    async with autotest_session_factory() as db:
        first = AutoTestScenario(name="登录", description="", is_active=True, user_id=7)
        second = AutoTestScenario(name="下单", description="", is_active=True, user_id=7)
        db.add_all([first, second])
        await db.commit()
        await db.refresh(first)
        await db.refresh(second)
        legacy_file.write_text(
            json.dumps(
                {
                    "legacy-login-order": {
                        "user_id": 7,
                        "name": "登录下单回归",
                        "scenario_ids": [second.id, first.id],
                    },
                }
            ),
            encoding="utf-8",
        )
        legacy_runs_file.write_text("{}", encoding="utf-8")
        await autotest_suites_router._migrate_legacy_suites(db, 7)

        suite = await db.scalar(select(SuiteModel).where(SuiteModel.legacy_key == "legacy-json:legacy-login-order"))
        assert suite is not None
        memberships = list(
            (
                await db.scalars(
                    select(SuiteScenarioModel)
                    .where(SuiteScenarioModel.suite_id == suite.id)
                    .order_by(SuiteScenarioModel.sort_order)
                )
            ).all()
        )
        assert [item.scenario_id for item in memberships] == [second.id, first.id]
        marker = await db.scalar(
            select(ImportJob).where(
                ImportJob.user_id == 7,
                ImportJob.source_type == "legacy_suite_json",
                ImportJob.status == "completed",
            )
        )
        assert marker is not None
        assert marker.summary["database_read_path_enabled"] is True
        assert (tmp_path / "legacy-backups").is_dir()
        assert list((tmp_path / "legacy-backups").glob("suites.json.*.readonly"))

    # The cut-over marker makes archived JSON read-only input. Later edits cannot
    # alter the database suite list or create a second suite.
    legacy_file.write_text(
        json.dumps(
            {
                "unexpected-later-edit": {"user_id": 7, "name": "不应再次导入", "scenario_ids": []},
            }
        ),
        encoding="utf-8",
    )
    async with autotest_session_factory() as db:
        await autotest_suites_router._migrate_legacy_suites(db, 7)
        suites = list((await db.scalars(select(SuiteModel).where(SuiteModel.user_id == 7))).all())
        assert len(suites) == 1


def test_mock_fault_config_is_normalized_and_rejects_unsafe_values():
    assert _validate_fault_config(
        "status_error",
        {"trigger_probability": "0.25", "random_seed": "fixed", "status_code": "503"},
    ) == {"trigger_probability": 0.25, "random_seed": "fixed", "status_code": 503}

    with pytest.raises(HTTPException) as probability_error:
        _validate_fault_config("delay", {"trigger_probability": 1.5})
    assert getattr(probability_error.value, "status_code", None) == 422

    with pytest.raises(HTTPException) as header_error:
        _validate_fault_config("custom_headers", {"headers": {"Bad\nHeader": "value"}})
    assert getattr(header_error.value, "status_code", None) == 422


def test_suite_notification_config_is_ssrf_safe_and_encrypted_at_rest():
    raw = suite_schedule_service.validate_notification_config(
        {
            "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/private-token",
            "notify_on": ["failed", "timed_out"],
            "enabled": True,
        }
    )
    stored = suite_schedule_service.protect_notification_config(raw)
    assert "private-token" not in str(stored)
    public = suite_schedule_service.notification_config_payload(stored)
    assert public["webhook_configured"] is True
    assert public["webhook_url"] == ""
    assert suite_schedule_service.notification_config_runtime(stored)["webhook_url"] == raw["webhook_url"]
    with pytest.raises(ValueError):
        suite_schedule_service.validate_notification_config(
            {
                "webhook_url": "http://127.0.0.1:5432/internal",
                "notify_on": ["failed"],
            }
        )


@pytest.mark.asyncio
async def test_mock_delay_and_custom_headers_are_real_faults():
    delayed = await mock_engine.generate_response(
        _rule(fault_type="delay", fault_config={"delay_ms": 0, "trigger_probability": 1})
    )
    assert delayed["status"] == 201
    assert delayed["headers"]["X-TestMaster-Fault"] == "delay"
    assert delayed["fault"]["triggered"] is True

    headers = await mock_engine.generate_response(
        _rule(
            fault_type="custom_headers",
            fault_config={
                "trigger_probability": 1,
                "headers": {"X-Trace-Test": "enabled", "Content-Length": "999", "Bad\nHeader": "blocked"},
            },
        )
    )
    assert headers["headers"]["X-Trace-Test"] == "enabled"
    assert "Content-Length" not in headers["headers"]
    assert headers["headers"]["X-TestMaster-Fault"] == "custom_headers"


@pytest.mark.asyncio
async def test_mock_log_persists_fault_decision(autotest_session_factory):
    async with autotest_session_factory() as db:
        project = MockProject(name="Audit Project", base_url_slug="audit-project", user_id=1)
        db.add(project)
        await db.flush()
        await mock_engine.log_request(
            db,
            project_id=project.id,
            rule_id=2,
            method="GET",
            path="/orders",
            request_headers={},
            request_body="",
            response_status=503,
            response_body='{"error":"fault"}',
            response_time_ms=20,
            matched_rule_name="failure rule",
            fault_decision={"triggered": True, "type": "status_error", "random_value": 0.1},
        )
        log = await db.get(MockRequestLog, 1)
        assert log.fault_triggered is True
        assert log.fault_type == "status_error"
        assert log.fault_random_value == pytest.approx(0.1)


@pytest.mark.asyncio
async def test_watchdog_marks_abandoned_execution_terminal(autotest_session_factory, monkeypatch):
    monkeypatch.setattr(suite_execution_service, "AsyncSessionLocal", autotest_session_factory)
    stale_at = datetime.now(timezone.utc) - timedelta(hours=1)
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="stale-execution",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="running",
            idempotency_key="stale-execution-key",
            started_at=stale_at,
            heartbeat_at=stale_at,
        )
        db.add(execution)
        await db.flush()
        db.add(
            AutomationExecutionItem(
                execution_id=execution.id,
                sequence=1,
                target_type="scenario",
                target_id=1,
                status="running",
            )
        )
        await db.commit()

    assert await suite_execution_service.reconcile_stale_suite_executions() == 1

    async with autotest_session_factory() as db:
        execution = await db.get(AutomationExecution, 1)
        item = await db.get(AutomationExecutionItem, 1)
        assert execution.status == "infra_error"
        assert execution.error_code == "RUNNER_HEARTBEAT_EXPIRED"
        assert item.status == "infra_error"


@pytest.mark.asyncio
async def test_ui_watchdog_marks_expired_agent_lease_terminal(autotest_session_factory):
    stale_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    async with autotest_session_factory() as db:
        agent = DesktopAgent(
            name="Expired runner",
            owner_id=1,
            agent_key="agent-expired",
            agent_token_hash="a" * 64,
            status="online",
            last_heartbeat_at=stale_at,
        )
        db.add(agent)
        await db.flush()
        run = UIRun(
            run_key="ui-stale-run",
            user_id=1,
            status="running",
            agent_id=agent.id,
            total_steps=1,
            artifact_manifest={"artifacts": [], "_last_sequence": 0},
            last_heartbeat_at=stale_at,
            lease_expires_at=stale_at,
        )
        db.add(run)
        await db.flush()
        execution = await run_service._ensure_authoritative_execution(db, run)
        execution.status = "running"
        execution.heartbeat_at = stale_at
        await db.commit()

    assert await agent_service.reconcile_stale_ui_runs(autotest_session_factory) == 1

    async with autotest_session_factory() as db:
        run = await db.scalar(select(UIRun).where(UIRun.run_key == "ui-stale-run"))
        execution = await db.get(AutomationExecution, run.automation_execution_id)
        agent = await db.get(DesktopAgent, run.agent_id)
        assert run.status == "infra_error"
        assert run.error_code == "RUNNER_HEARTBEAT_EXPIRED"
        assert execution.status == "infra_error"
        assert agent.status == "offline"


@pytest.mark.asyncio
async def test_artifact_download_validates_owner_and_storage(
    autotest_client, autotest_session_factory, monkeypatch, tmp_path
):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    artifact_root = Path(tmp_path) / "artifacts" / "objects" / "7" / "evidence"
    artifact_root.mkdir(parents=True)
    content = b"diagnostic screenshot"
    (artifact_root / "failure.png").write_bytes(content)
    monkeypatch.setenv("TESTMASTER_DATA_DIR", str(tmp_path))

    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="artifact-execution",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="failed",
            idempotency_key="artifact-execution-key",
        )
        db.add(execution)
        await db.flush()
        artifact = ArtifactManifest(
            execution_id=execution.id,
            kind="screenshot",
            filename="failure.png",
            content_type="image/png",
            size_bytes=len(content),
            sha256="a" * 64,
            storage_key="7/evidence/failure.png",
            retention_until=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        artifact_id = artifact.id

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    app.dependency_overrides[get_current_user] = _admin_user
    response = autotest_client.get(f"/api/auto-test/artifacts/{artifact_id}/content")
    assert response.status_code == 200
    assert response.content == content
    assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.asyncio
async def test_artifact_chunk_retry_trims_uncommitted_bytes(
    autotest_client, autotest_session_factory, monkeypatch, tmp_path
):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app
    import hashlib

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    content = b"abcdef"
    monkeypatch.setenv("TESTMASTER_DATA_DIR", str(tmp_path))
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="resume-execution",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="failed",
            idempotency_key="resume-execution-key",
        )
        db.add(execution)
        await db.commit()

    app.dependency_overrides[get_current_user] = _admin_user
    created = autotest_client.post(
        "/api/auto-test/artifacts/upload-sessions",
        json={
            "execution_id": "resume-execution",
            "kind": "log",
            "filename": "run.log",
            "content_type": "text/plain",
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    )
    assert created.status_code == 201
    upload_id = created.json()["upload_id"]
    progress = autotest_client.get(f"/api/auto-test/artifacts/upload-sessions/{upload_id}")
    assert progress.status_code == 200
    assert progress.json()["received_bytes"] == 0
    temporary_path = Path(tmp_path) / "artifacts" / "tmp" / f"{upload_id}.part"
    temporary_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path.write_bytes(b"abc-uncommitted")
    async with autotest_session_factory() as db:
        session = await db.get(ArtifactUploadSession, upload_id)
        session.received_bytes = 3
        await db.commit()

    uploaded = autotest_client.put(
        f"/api/auto-test/artifacts/upload-sessions/{upload_id}/content",
        content=b"def",
        headers={"Content-Range": "bytes 3-5/6"},
    )
    assert uploaded.status_code == 204
    completed = autotest_client.post(f"/api/auto-test/artifacts/upload-sessions/{upload_id}/complete")
    assert completed.status_code == 200
    repeated_complete = autotest_client.post(f"/api/auto-test/artifacts/upload-sessions/{upload_id}/complete")
    assert repeated_complete.status_code == 200
    assert repeated_complete.json()["artifact_id"] == completed.json()["artifact_id"]


@pytest.mark.asyncio
async def test_artifact_maintenance_removes_expired_files_and_metadata(autotest_session_factory, tmp_path):
    now = datetime.now(timezone.utc)
    root = Path(tmp_path) / "artifacts"
    artifact_path = root / "objects" / "8" / "expired" / "run.log"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"expired")
    temp_path = root / "tmp" / "expired-upload.part"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(b"partial")

    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="expired-artifact-execution",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="failed",
            idempotency_key="expired-artifact-execution-key",
        )
        db.add(execution)
        await db.flush()
        artifact = ArtifactManifest(
            execution_id=execution.id,
            kind="log",
            filename="run.log",
            content_type="text/plain",
            size_bytes=7,
            sha256="b" * 64,
            storage_key="8/expired/run.log",
            retention_until=now - timedelta(minutes=1),
        )
        upload = ArtifactUploadSession(
            id="expired-upload-session",
            execution_id=execution.id,
            user_id=1,
            kind="log",
            filename="run.log",
            content_type="text/plain",
            expected_size_bytes=7,
            expected_sha256="c" * 64,
            temp_storage_key="expired-upload.part",
            expires_at=now - timedelta(minutes=1),
        )
        db.add_all([artifact, upload])
        await db.commit()
        artifact_id = artifact.id

    result = await cleanup_expired_artifacts(
        session_factory=autotest_session_factory,
        storage_root=root,
        now=now,
    )
    assert result["expired_uploads"] == 1
    assert result["deleted_artifacts"] == 1
    assert not artifact_path.exists()
    assert not temp_path.exists()

    async with autotest_session_factory() as db:
        assert await db.get(ArtifactManifest, artifact_id) is None
        upload = await db.get(ArtifactUploadSession, "expired-upload-session")
        assert upload.status == "expired"


@pytest.mark.asyncio
async def test_capture_session_redacts_then_converts_confirmed_flow(autotest_client, autotest_session_factory):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    app.dependency_overrides[get_current_user] = _admin_user
    created = autotest_client.post(
        "/api/auto-test/import/captures",
        json={
            "origin": "desktop_browser",
            "source_url": "https://shop.example.test/start?token=session-secret&tab=orders",
        },
    )
    assert created.status_code == 201
    session_id = created.json()["id"]
    appended = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges",
        json={
            "exchanges": [
                {
                    "method": "POST",
                    "url": "https://shop.example.test/login?token=secret",
                    "resourceType": "fetch",
                    "requestHeaders": {"Authorization": "Bearer secret", "Content-Type": "application/json"},
                    "requestBody": {"username": "buyer", "password": "secret"},
                    "responseHeaders": {"Content-Type": "application/json"},
                    "responseBody": {"token": "real-token"},
                    "status": 200,
                },
                {
                    "method": "POST",
                    "url": "https://shop.example.test/orders",
                    "resourceType": "xhr",
                    "requestHeaders": {"Authorization": "Bearer real-token", "Content-Type": "application/json"},
                    "requestBody": {"sku": "A-1"},
                    "responseBody": {"order_id": "O-1"},
                    "status": 201,
                },
            ]
        },
    )
    assert appended.status_code == 200
    exchange_ids = appended.json()["exchange_ids"]
    assert len(exchange_ids) == 2
    assert autotest_client.post(f"/api/auto-test/import/captures/{session_id}/complete").status_code == 200
    preview = autotest_client.get(f"/api/auto-test/import/captures/{session_id}")
    assert preview.status_code == 200
    assert "session-secret" not in preview.json()["source_url"]
    assert preview.json()["source_url"].endswith("token={{TOKEN}}&tab=orders")
    assert preview.json()["candidates"][0]["headers"]["Authorization"] == "{{AUTHORIZATION}}"
    assert preview.json()["candidates"][0]["payload"]["password"] == "{{PASSWORD}}"

    converted = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/convert",
        json={
            "exchange_ids": exchange_ids,
            "create_scenario": True,
            "confirm_dependency_review": True,
            "scenario_name": "login to order",
            "variable_mappings": [
                {
                    "source_exchange_id": exchange_ids[0],
                    "variable_name": "access_token",
                    "json_path": "$.token",
                    "targets": [
                        {
                            "exchange_id": exchange_ids[1],
                            "location": "headers.Authorization",
                            "template": "Bearer {{access_token}}",
                        }
                    ],
                }
            ],
        },
    )
    assert converted.status_code == 200
    data = converted.json()
    assert data["imported_count"] == 2
    assert data["scenario_id"]
    assert data["requires_preview"] is True
    async with autotest_session_factory() as db:
        scenario = await db.get(AutoTestScenario, data["scenario_id"])
        assert scenario.name == "login to order"
        steps = list(
            (
                await db.scalars(select(AutoTestScenarioStep).where(AutoTestScenarioStep.scenario_id == scenario.id))
            ).all()
        )
        assert len(steps) == 2


@pytest.mark.asyncio
async def test_suite_schedule_configuration_is_persistent_and_validated(autotest_client, autotest_session_factory):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app
    from fastapi_backend.services.autotest_scheduler import stop_scheduler

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    async with autotest_session_factory() as db:
        scenario = AutoTestScenario(name="scheduled scenario", user_id=1, is_active=True)
        db.add(scenario)
        await db.flush()
        suite = SuiteModel(name="scheduled suite", user_id=1, kind="scenario", is_active=True)
        db.add(suite)
        await db.flush()
        db.add(SuiteScenarioModel(suite_id=suite.id, scenario_id=scenario.id, sort_order=0))
        await db.commit()
        suite_id = suite.id

    app.dependency_overrides[get_current_user] = _admin_user
    try:
        invalid = autotest_client.put(
            f"/api/auto-test/suites/{suite_id}/schedule",
            json={"cron_expression": "not cron", "timezone_name": "Asia/Shanghai"},
        )
        assert invalid.status_code == 422
        response = autotest_client.put(
            f"/api/auto-test/suites/{suite_id}/schedule",
            json={
                "cron_expression": "0 9 * * 1-5",
                "timezone_name": "Asia/Shanghai",
                "misfire_policy": "coalesce",
                "max_concurrent": 1,
                "execution_timeout_seconds": 120,
                "max_retries": 2,
                "is_active": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["schedule"]["cron_expression"] == "0 9 * * 1-5"
        fetched = autotest_client.get(f"/api/auto-test/suites/{suite_id}/schedule")
        assert fetched.status_code == 200
        assert fetched.json()["schedule"]["timezone_name"] == "Asia/Shanghai"
        assert fetched.json()["schedule"]["execution_timeout_seconds"] == 120
        assert fetched.json()["schedule"]["max_retries"] == 2
        deleted = autotest_client.delete(f"/api/auto-test/suites/{suite_id}/schedule")
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True
    finally:
        stop_scheduler()


@pytest.mark.asyncio
async def test_scheduled_suite_uses_occurrence_idempotency(autotest_session_factory, monkeypatch):
    monkeypatch.setattr(suite_schedule_service, "AsyncSessionLocal", autotest_session_factory)
    dispatched = []

    async def _dispatch(execution_id):
        dispatched.append(execution_id)

    monkeypatch.setattr(suite_schedule_service, "dispatch_suite_execution", _dispatch)
    async with autotest_session_factory() as db:
        scenario = AutoTestScenario(name="lease scenario", user_id=1, is_active=True)
        suite = SuiteModel(name="lease suite", user_id=1, kind="scenario", is_active=True)
        db.add_all([scenario, suite])
        await db.flush()
        db.add(SuiteScenarioModel(suite_id=suite.id, scenario_id=scenario.id, sort_order=0))
        schedule = SuiteScheduleModel(
            suite_id=suite.id,
            cron_expression="* * * * *",
            timezone_name="Asia/Shanghai",
            is_active=True,
            max_concurrent=1,
            misfire_policy="coalesce",
        )
        db.add(schedule)
        await db.commit()
        schedule_id = schedule.id

    await suite_schedule_service.execute_scheduled_suite(schedule_id)
    await suite_schedule_service.execute_scheduled_suite(schedule_id)

    async with autotest_session_factory() as db:
        executions = list((await db.scalars(select(AutomationExecution))).all())
        assert len(executions) == 1
        assert executions[0].result_summary["trigger"] == "schedule"
    # A still-queued occurrence is deliberately re-dispatched so a process
    # crash after the DB commit cannot strand it forever. The runner claim is
    # atomic, therefore duplicate broker messages remain harmless.
    assert dispatched == [executions[0].id, executions[0].id]


@pytest.mark.asyncio
async def test_suite_runner_ignores_a_duplicate_dispatch_after_claim(autotest_session_factory, monkeypatch):
    monkeypatch.setattr(suite_execution_service, "AsyncSessionLocal", autotest_session_factory)
    calls: list[int] = []

    async def _run_scenario(scenario_id, **_kwargs):
        calls.append(scenario_id)
        return {"success": True, "success_steps": 1, "failed_steps": 0}

    monkeypatch.setattr(suite_execution_service, "run_scenario", _run_scenario)
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="duplicate-dispatch-execution",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="queued",
            idempotency_key="duplicate-dispatch-key",
        )
        db.add(execution)
        await db.flush()
        db.add(
            AutomationExecutionItem(
                execution_id=execution.id,
                sequence=1,
                target_type="scenario",
                target_id=99,
                target_name="duplicate guard",
                status="queued",
            )
        )
        await db.commit()
        execution_id = execution.id

    await suite_execution_service.run_suite_execution(execution_id, runner_id="first-dispatch")
    await suite_execution_service.run_suite_execution(execution_id, runner_id="duplicate-dispatch")

    assert calls == [99]
    async with autotest_session_factory() as db:
        execution = await db.get(AutomationExecution, execution_id)
        assert execution.status == "passed"
        assert execution.runner_id == "first-dispatch"


@pytest.mark.asyncio
async def test_suite_runner_creates_a_distinct_retry_attempt(autotest_session_factory, monkeypatch):
    monkeypatch.setattr(suite_execution_service, "AsyncSessionLocal", autotest_session_factory)
    dispatched: list[int] = []

    async def _failed_scenario(*_args, **_kwargs):
        return {"success": False, "success_steps": 0, "failed_steps": 1}

    async def _dispatch(execution_id: int):
        dispatched.append(execution_id)

    monkeypatch.setattr(suite_execution_service, "run_scenario", _failed_scenario)
    monkeypatch.setattr(suite_execution_service, "dispatch_suite_execution", _dispatch)
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="retry-parent",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="queued",
            idempotency_key="retry-parent-key",
            result_summary={"execution_timeout_seconds": 30, "max_retries": 1, "trigger": "schedule"},
        )
        db.add(execution)
        await db.flush()
        db.add(
            AutomationExecutionItem(
                execution_id=execution.id,
                sequence=1,
                target_type="scenario",
                target_id=7,
                target_name="will retry",
                status="queued",
            )
        )
        await db.commit()
        parent_id = execution.id

    await suite_execution_service.run_suite_execution(parent_id, runner_id="retry-test")

    async with autotest_session_factory() as db:
        executions = list((await db.scalars(select(AutomationExecution).order_by(AutomationExecution.id))).all())
        assert len(executions) == 2
        parent, retry = executions
        assert parent.status == "failed"
        assert parent.attempt == 1
        assert retry.status == "queued"
        assert retry.attempt == 2
        assert retry.result_summary["retry_of_execution_id"] == parent.public_id
        assert retry.idempotency_key != parent.idempotency_key
        retry_items = list(
            (
                await db.scalars(
                    select(AutomationExecutionItem).where(AutomationExecutionItem.execution_id == retry.id)
                )
            ).all()
        )
        assert [(item.target_id, item.status) for item in retry_items] == [(7, "queued")]
    assert dispatched == [retry.id]


@pytest.mark.asyncio
async def test_suite_runner_marks_total_execution_timeout_terminal(autotest_session_factory, monkeypatch):
    monkeypatch.setattr(suite_execution_service, "AsyncSessionLocal", autotest_session_factory)

    async def _slow_scenario(*_args, **_kwargs):
        await asyncio.sleep(0.05)
        return {"success": True, "success_steps": 1, "failed_steps": 0}

    monkeypatch.setattr(suite_execution_service, "run_scenario", _slow_scenario)
    monkeypatch.setattr(
        suite_execution_service,
        "_execution_policy",
        lambda _execution: (0.001, 0, "retry:timeout-test", {}),
    )
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="timeout-parent",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="queued",
            idempotency_key="timeout-parent-key",
        )
        db.add(execution)
        await db.flush()
        db.add_all(
            [
                AutomationExecutionItem(
                    execution_id=execution.id, sequence=1, target_type="scenario", target_id=8, status="queued"
                ),
                AutomationExecutionItem(
                    execution_id=execution.id, sequence=2, target_type="scenario", target_id=9, status="queued"
                ),
            ]
        )
        await db.commit()
        execution_id = execution.id

    await suite_execution_service.run_suite_execution(execution_id, runner_id="timeout-test")

    async with autotest_session_factory() as db:
        execution = await db.get(AutomationExecution, execution_id)
        items = list(
            (
                await db.scalars(
                    select(AutomationExecutionItem)
                    .where(AutomationExecutionItem.execution_id == execution_id)
                    .order_by(AutomationExecutionItem.sequence)
                )
            ).all()
        )
        assert execution.status == "timed_out"
        assert execution.error_code == "EXECUTION_TIMEOUT"
        assert [item.status for item in items] == ["timed_out", "skipped"]


@pytest.mark.asyncio
async def test_inactive_suite_cannot_run_and_queued_cancel_finishes_all_items(
    autotest_client, autotest_session_factory
):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    async with autotest_session_factory() as db:
        scenario = AutoTestScenario(name="active member", user_id=1, is_active=True)
        inactive_suite = SuiteModel(name="inactive suite", user_id=1, kind="scenario", is_active=False)
        db.add_all([scenario, inactive_suite])
        await db.flush()
        db.add(SuiteScenarioModel(suite_id=inactive_suite.id, scenario_id=scenario.id, sort_order=0))
        execution = AutomationExecution(
            public_id="cancel-before-run",
            execution_type="suite",
            target_type="suite",
            target_id=inactive_suite.id,
            user_id=1,
            status="queued",
            idempotency_key="cancel-before-run-key",
        )
        db.add(execution)
        await db.flush()
        db.add_all(
            [
                AutomationExecutionItem(
                    execution_id=execution.id,
                    sequence=1,
                    target_type="scenario",
                    target_id=scenario.id,
                    status="queued",
                ),
                AutomationExecutionItem(
                    execution_id=execution.id,
                    sequence=2,
                    target_type="scenario",
                    target_id=scenario.id,
                    status="queued",
                ),
            ]
        )
        await db.commit()
        suite_id = inactive_suite.id
        execution_id = execution.id

    app.dependency_overrides[get_current_user] = _admin_user
    inactive_run = autotest_client.post(f"/api/auto-test/suites/{suite_id}/executions", json={})
    assert inactive_run.status_code == 409, inactive_run.text
    cancelled = autotest_client.post("/api/auto-test/suites/executions/cancel-before-run/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
    async with autotest_session_factory() as db:
        items = list(
            (
                await db.scalars(
                    select(AutomationExecutionItem)
                    .where(AutomationExecutionItem.execution_id == execution_id)
                    .order_by(AutomationExecutionItem.sequence)
                )
            ).all()
        )
        assert [item.status for item in items] == ["cancelled", "cancelled"]


@pytest.mark.asyncio
async def test_suite_schedule_rejects_string_boolean_and_accepts_json_boolean(
    autotest_client, autotest_session_factory, monkeypatch
):
    """A JSON string must never silently enable a schedule."""
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    app.dependency_overrides[get_current_user] = _admin_user
    monkeypatch.setattr(autotest_suites_router, "install_suite_schedule_job", lambda _schedule: None)
    async with autotest_session_factory() as db:
        suite = SuiteModel(name="schedule boolean", user_id=1, kind="scenario", is_active=True)
        db.add(suite)
        await db.commit()
        await db.refresh(suite)
        suite_id = suite.id

    invalid = autotest_client.put(
        f"/api/auto-test/suites/{suite_id}/schedule",
        json={"cron_expression": "0 9 * * *", "is_active": "false"},
    )
    assert invalid.status_code == 422, invalid.text

    valid = autotest_client.put(
        f"/api/auto-test/suites/{suite_id}/schedule",
        json={"cron_expression": "0 9 * * *", "is_active": False},
    )
    assert valid.status_code == 200, valid.text
    assert valid.json()["schedule"]["is_active"] is False


@pytest.mark.asyncio
async def test_watchdog_recovers_stale_queued_execution(autotest_session_factory, monkeypatch):
    """A durable row must be retried when the broker loses its delivery message."""
    stale_at = datetime.now(timezone.utc) - timedelta(hours=1)
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="queued-recovery",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="queued",
            idempotency_key="queued-recovery-key",
            queued_at=stale_at,
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        execution_id = execution.id

    dispatched: list[int] = []

    async def _dispatch(candidate_id: int):
        dispatched.append(candidate_id)

    monkeypatch.setattr(suite_execution_service, "AsyncSessionLocal", autotest_session_factory)
    monkeypatch.setattr(suite_execution_service, "dispatch_suite_execution", _dispatch)
    assert await suite_execution_service.reconcile_stale_suite_executions() == 1
    assert dispatched == [execution_id]

    async with autotest_session_factory() as db:
        recovered = await db.get(AutomationExecution, execution_id)
        assert recovered.status == "queued"
        assert recovered.heartbeat_at is not None
        events = list(
            (await db.scalars(select(ExecutionEvent).where(ExecutionEvent.execution_id == execution_id))).all()
        )
        assert [event.event_type for event in events] == ["execution_recovery_dispatch"]


@pytest.mark.asyncio
async def test_heartbeat_loop_keeps_long_running_execution_alive(autotest_session_factory, monkeypatch):
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="heartbeat-long-run",
            execution_type="suite",
            target_type="suite",
            target_id=1,
            user_id=1,
            status="running",
            idempotency_key="heartbeat-long-run-key",
            heartbeat_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        execution_id = execution.id

    monkeypatch.setattr(suite_execution_service, "AsyncSessionLocal", autotest_session_factory)
    monkeypatch.setattr(suite_execution_service, "_HEARTBEAT_INTERVAL_SECONDS", 0.01)
    heartbeat = asyncio.create_task(suite_execution_service._maintain_execution_heartbeat(execution_id, 1))
    await asyncio.sleep(0.03)
    async with autotest_session_factory() as db:
        execution = await db.get(AutomationExecution, execution_id)
        heartbeat_at = execution.heartbeat_at
        if heartbeat_at.tzinfo is None:
            heartbeat_at = heartbeat_at.replace(tzinfo=timezone.utc)
        assert heartbeat_at > datetime.now(timezone.utc) - timedelta(seconds=1)
        execution.status = "passed"
        await db.commit()
    await heartbeat


@pytest.mark.asyncio
async def test_watchdog_retries_after_a_transient_failure(monkeypatch):
    calls = 0
    completed = asyncio.Event()

    async def _reconcile():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary database outage")
        completed.set()

    monkeypatch.setattr(suite_execution_service, "reconcile_stale_suite_executions", _reconcile)
    monkeypatch.setattr(suite_execution_service, "_WATCHDOG_INTERVAL_SECONDS", 0.01)
    task = asyncio.create_task(suite_execution_service._watchdog_loop())
    try:
        await asyncio.wait_for(completed.wait(), timeout=1)
        assert calls >= 2
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_suite_terminal_notification_records_delivery_event(autotest_session_factory, monkeypatch):
    async with autotest_session_factory() as db:
        execution = AutomationExecution(
            public_id="notify-result",
            execution_type="suite",
            target_type="suite",
            target_id=42,
            user_id=1,
            status="failed",
            idempotency_key="notify-result-key",
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        execution_id = execution.id
    stored_config = suite_schedule_service.protect_notification_config(
        suite_schedule_service.validate_notification_config(
            {
                "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=fake",
                "notify_on": ["failed"],
            }
        )
    )
    sent: list[str] = []

    async def _send(url: str, text: str):
        sent.append(url)
        return True, "ok"

    monkeypatch.setattr(suite_execution_service, "AsyncSessionLocal", autotest_session_factory)
    monkeypatch.setattr("fastapi_backend.services.webhook_notify.send_bot_webhook_async", _send)
    await suite_execution_service._notify_execution_result(
        execution_id,
        {
            "notification_config": stored_config,
            "status": "failed",
            "suite_id": 42,
            "public_id": "notify-result",
            "attempt": 1,
            "passed": 0,
            "failed": 1,
            "timed_out": 0,
            "cancelled": 0,
            "duration_ms": 12,
        },
    )
    assert sent == ["https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=fake"]
    async with autotest_session_factory() as db:
        events = list(
            (await db.scalars(select(ExecutionEvent).where(ExecutionEvent.execution_id == execution_id))).all()
        )
        assert [event.event_type for event in events] == ["notification_delivered"]
