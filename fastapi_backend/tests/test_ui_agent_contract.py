import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from fastapi_backend.core.config import settings
from fastapi_backend.deps.auth import get_current_active_user, get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import (
    ArtifactManifest,
    AutoTestEnvironment,
    AutoTestGlobalVariable,
    ExecutionEvent,
)
from fastapi_backend.models.models import AuditLog
from fastapi_backend.models.ui_automation import DesktopAgent, UIArtifact, UIRun
from fastapi_backend.services.ui_automation import agent_service
from fastapi_backend.utils.encryption import encrypt


@pytest.fixture(autouse=True)
def ui_agent_user():
    original = settings.UI_AUTOMATION_ENABLED
    settings.UI_AUTOMATION_ENABLED = True

    async def current_user():
        return SimpleNamespace(
            id=1,
            username="agent-owner",
            is_active=True,
            is_admin=True,
            is_super_admin=True,
            role_id=None,
        )

    app.dependency_overrides[get_current_user] = current_user
    app.dependency_overrides[get_current_active_user] = current_user
    yield
    settings.UI_AUTOMATION_ENABLED = original
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_active_user, None)


def _create_case_version(client) -> tuple[int, int]:
    case_response = client.post("/api/ui-automation/cases", json={"name": "Agent contract case"})
    assert case_response.status_code == 200, case_response.text
    case_id = case_response.json()["id"]
    steps = client.put(
        f"/api/ui-automation/cases/{case_id}/steps",
        json={
            "steps": [
                {
                    "id": "agent-step-1",
                    "order": 10,
                    "type": "goto",
                    "input": {"url": "{{base_url}}/login"},
                }
            ]
        },
    )
    assert steps.status_code == 200, steps.text
    version = client.post(f"/api/ui-automation/cases/{case_id}/versions", json={})
    assert version.status_code == 200, version.text
    return case_id, version.json()["id"]


def _register_agent(client, *, max_parallel: int = 1) -> dict:
    response = client.post(
        "/api/ui-automation/agents",
        json={
            "name": "Managed Windows Agent",
            "hostname": "qa-agent-01",
            "capabilities": {"chromium": True},
            "max_parallel": max_parallel,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _queue_and_claim(client, agent: dict, case_id: int, version_id: int, **run_fields) -> tuple[dict, dict]:
    queued = client.post(
        "/api/ui-automation/runs",
        json={
            "case_id": case_id,
            "case_version_id": version_id,
            "agent_id": agent["id"],
            "trigger_type": "scheduled",
            **run_fields,
        },
    )
    assert queued.status_code == 200, queued.text
    claim = client.post(
        f"/api/ui-automation/agents/{agent['id']}/claim",
        headers={"X-TestMaster-Agent-Token": agent["bootstrap_token"]},
    )
    assert claim.status_code == 200, claim.text
    assert claim.json()["run"]["id"] == queued.json()["id"]
    return queued.json(), claim.json()


@pytest.mark.asyncio
async def test_agent_claim_resolves_owner_environment_without_persisting_secrets(client, db_session):
    environment = AutoTestEnvironment(
        env_name="Agent staging",
        base_url="https://staging.example.test",
        variables={"ORDER_TOKEN": "environment-secret", "REGION": "hk"},
        services=[{"name": "orders", "base_url": "https://orders.example.test"}],
        user_id=1,
    )
    db_session.add_all(
        [
            environment,
            AutoTestGlobalVariable(
                name="LOGIN_PASSWORD",
                value=encrypt("global-secret"),
                is_encrypted=True,
                user_id=1,
            ),
        ]
    )
    await db_session.commit()
    await db_session.refresh(environment)

    case_id, version_id = _create_case_version(client)
    agent = _register_agent(client)
    queued, claimed = _queue_and_claim(
        client,
        agent,
        case_id,
        version_id,
        environment_id=environment.id,
        client_run_key="agent-runtime-contract",
    )

    runtime = claimed["plan"]["environment"]
    assert runtime["id"] == environment.id
    assert runtime["base_url"] == "https://staging.example.test"
    assert runtime["variables"]["LOGIN_PASSWORD"] == "global-secret"
    assert runtime["variables"]["ORDER_TOKEN"] == "environment-secret"
    assert {"LOGIN_PASSWORD", "ORDER_TOKEN"}.issubset(runtime["secret_keys"])

    stored_run = await db_session.get(UIRun, queued["id"])
    events = list(
        (
            await db_session.scalars(
                select(ExecutionEvent).where(ExecutionEvent.execution_id == stored_run.automation_execution_id)
            )
        ).all()
    )
    persisted = f"{stored_run.artifact_manifest} {[(event.event_type, event.payload_redacted) for event in events]}"
    assert "global-secret" not in persisted
    assert "environment-secret" not in persisted


@pytest.mark.asyncio
async def test_agent_claim_and_token_are_strictly_owner_scoped(client, db_session):
    case_id, version_id = _create_case_version(client)
    owner_agent = _register_agent(client)
    foreign_agent, foreign_token = await agent_service.register_agent(db_session, 2, {"name": "Foreign Agent"})
    orphaned_cross_owner_run = UIRun(
        run_key="cross-owner-corrupt-run",
        case_id=case_id,
        case_version_id=version_id,
        agent_id=owner_agent["id"],
        trigger_type="scheduled",
        status="waiting_for_agent",
        total_steps=1,
        artifact_manifest={"artifacts": [], "_last_sequence": 0},
        user_id=2,
    )
    db_session.add(orphaned_cross_owner_run)
    await db_session.commit()

    wrong_token = client.post(
        f"/api/ui-automation/agents/{owner_agent['id']}/claim",
        headers={"X-TestMaster-Agent-Token": foreign_token},
    )
    assert wrong_token.status_code == 401
    owner_claim = client.post(
        f"/api/ui-automation/agents/{owner_agent['id']}/claim",
        headers={"X-TestMaster-Agent-Token": owner_agent["bootstrap_token"]},
    )
    assert owner_claim.status_code == 200
    assert owner_claim.json()["run"] is None
    assert foreign_agent.owner_id == 2


@pytest.mark.asyncio
async def test_agent_can_resumably_upload_and_link_only_to_its_active_run(client, db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("TESTMASTER_DATA_DIR", str(tmp_path))
    case_id, version_id = _create_case_version(client)
    agent = _register_agent(client, max_parallel=2)
    first_run, _ = _queue_and_claim(client, agent, case_id, version_id, client_run_key="agent-artifact-first")
    second_run, _ = _queue_and_claim(client, agent, case_id, version_id, client_run_key="agent-artifact-second")
    content = b"playwright-trace-content"
    headers = {"X-TestMaster-Agent-Token": agent["bootstrap_token"]}
    created = client.post(
        f"/api/ui-automation/agents/{agent['id']}/runs/{first_run['id']}/artifacts/upload-sessions",
        headers=headers,
        json={
            "kind": "trace",
            "filename": "trace.zip",
            "content_type": "application/zip",
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    )
    assert created.status_code == 201, created.text
    upload = created.json()
    progress = client.get(
        f"/api/ui-automation/agents/{agent['id']}/runs/{first_run['id']}/artifacts/upload-sessions/{upload['upload_id']}",
        headers=headers,
    )
    assert progress.status_code == 200, progress.text
    assert progress.json()["received_bytes"] == 0

    cross_run = client.put(
        f"/api/ui-automation/agents/{agent['id']}/runs/{second_run['id']}/artifacts/upload-sessions/{upload['upload_id']}/content",
        headers={**headers, "Content-Range": f"bytes 0-{len(content) - 1}/{len(content)}"},
        content=content,
    )
    assert cross_run.status_code == 404

    uploaded = client.put(
        upload["chunk_endpoint"],
        headers={**headers, "Content-Range": f"bytes 0-{len(content) - 1}/{len(content)}"},
        content=content,
    )
    assert uploaded.status_code == 204, uploaded.text
    progressed = client.get(
        f"/api/ui-automation/agents/{agent['id']}/runs/{first_run['id']}/artifacts/upload-sessions/{upload['upload_id']}",
        headers=headers,
    )
    assert progressed.status_code == 200, progressed.text
    assert progressed.json()["received_bytes"] == len(content)
    completed = client.post(
        f"/api/ui-automation/agents/{agent['id']}/runs/{first_run['id']}/artifacts/upload-sessions/{upload['upload_id']}/complete",
        headers=headers,
    )
    assert completed.status_code == 200, completed.text
    result = completed.json()
    assert result["linked_artifact"]["artifact_manifest_id"] == result["artifact_id"]

    artifact = await db_session.get(ArtifactManifest, result["artifact_id"])
    linked = await db_session.scalar(select(UIArtifact).where(UIArtifact.artifact_manifest_id == artifact.id))
    first_stored = await db_session.get(UIRun, first_run["id"])
    assert artifact.execution_id == first_stored.automation_execution_id
    assert linked.run_id == first_stored.id

    first_stored.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()
    expired = client.post(
        f"/api/ui-automation/agents/{agent['id']}/runs/{first_run['id']}/artifacts/upload-sessions",
        headers=headers,
        json={
            "kind": "log",
            "filename": "late.log",
            "content_type": "text/plain",
            "size_bytes": 1,
            "sha256": hashlib.sha256(b"x").hexdigest(),
        },
    )
    assert expired.status_code == 409


@pytest.mark.asyncio
async def test_revoking_agent_is_idempotent_invalidates_token_and_terminalizes_runs(client, db_session):
    case_id, version_id = _create_case_version(client)
    agent = _register_agent(client)
    queued = client.post(
        "/api/ui-automation/runs",
        json={
            "case_id": case_id,
            "case_version_id": version_id,
            "agent_id": agent["id"],
            "trigger_type": "scheduled",
            "client_run_key": "revoked-agent-run",
        },
    )
    assert queued.status_code == 200, queued.text

    revoked = client.delete(f"/api/ui-automation/agents/{agent['id']}")
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["revoked_at"] is not None
    repeated = client.delete(f"/api/ui-automation/agents/{agent['id']}")
    assert repeated.status_code == 200
    assert repeated.json()["revoked_at"] == revoked.json()["revoked_at"]

    heartbeat = client.post(
        f"/api/ui-automation/agents/{agent['id']}/heartbeat",
        headers={"X-TestMaster-Agent-Token": agent["bootstrap_token"]},
    )
    assert heartbeat.status_code == 401
    run = await db_session.get(UIRun, queued.json()["id"])
    assert run.status == "infra_error"
    assert run.error_code == "AGENT_REVOKED"
    assert await db_session.scalar(select(AuditLog).where(AuditLog.action == "revoke")) is not None

    foreign = DesktopAgent(name="Other owner agent", owner_id=2, status="offline")
    db_session.add(foreign)
    await db_session.commit()
    denied = client.delete(f"/api/ui-automation/agents/{foreign.id}")
    assert denied.status_code == 404


@pytest.mark.asyncio
async def test_ui_watchdog_retries_after_transient_failure(monkeypatch):
    calls = 0

    async def no_wait(_seconds):
        return None

    async def flaky_reconcile():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary database outage")
        raise asyncio.CancelledError

    monkeypatch.setattr(agent_service.asyncio, "sleep", no_wait)
    monkeypatch.setattr(agent_service, "reconcile_stale_ui_runs", flaky_reconcile)
    with pytest.raises(asyncio.CancelledError):
        await agent_service._watchdog_loop()
    assert calls == 2


@pytest.mark.asyncio
async def test_agent_heartbeat_renews_claimed_run_lease(client, db_session):
    case_id, version_id = _create_case_version(client)
    agent = _register_agent(client)
    queued, _ = _queue_and_claim(client, agent, case_id, version_id, client_run_key="renew-lease")
    stored = await db_session.get(UIRun, queued["id"])
    stored.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()

    response = client.post(
        f"/api/ui-automation/agents/{agent['id']}/heartbeat",
        headers={"X-TestMaster-Agent-Token": agent["bootstrap_token"]},
    )
    assert response.status_code == 200, response.text
    await db_session.refresh(stored)
    expires_at = stored.lease_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at > datetime.now(timezone.utc)
    assert response.json()["cancel_run_ids"] == []


@pytest.mark.asyncio
async def test_cancel_unclaimed_run_terminalizes_immediately(client, db_session):
    case_id, version_id = _create_case_version(client)
    created = client.post(
        "/api/ui-automation/runs",
        json={
            "case_id": case_id,
            "case_version_id": version_id,
            "trigger_type": "manual",
            "client_run_key": "cancel-before-claim",
        },
    )
    assert created.status_code == 200, created.text
    cancelled = client.post(f"/api/ui-automation/runs/{created.json()['id']}/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
    stored = await db_session.get(UIRun, created.json()["id"])
    assert stored.finished_at is not None
    assert stored.lease_expires_at is None
    assert stored.error_code == "CANCELLED_BY_USER"


@pytest.mark.asyncio
async def test_cancel_active_run_is_delivered_to_agent_and_acknowledged(client, db_session):
    case_id, version_id = _create_case_version(client)
    agent = _register_agent(client)
    queued, _ = _queue_and_claim(client, agent, case_id, version_id, client_run_key="cancel-active")
    requested = client.post(f"/api/ui-automation/runs/{queued['id']}/cancel")
    assert requested.status_code == 200, requested.text
    assert requested.json()["status"] == "cancel_requested"
    headers = {"X-TestMaster-Agent-Token": agent["bootstrap_token"]}
    heartbeat = client.post(f"/api/ui-automation/agents/{agent['id']}/heartbeat", headers=headers)
    assert heartbeat.status_code == 200, heartbeat.text
    assert heartbeat.json()["cancel_run_ids"] == [queued["id"]]
    finished = client.post(
        f"/api/ui-automation/agents/{agent['id']}/runs/{queued['id']}/events",
        headers=headers,
        json={"events": [{"sequence": 1, "type": "run:finish", "status": "cancelled"}]},
    )
    assert finished.status_code == 200, finished.text
    assert finished.json()["status"] == "cancelled"
    stored = await db_session.get(UIRun, queued["id"])
    assert stored.status == "cancelled"
    assert stored.lease_expires_at is None


@pytest.mark.asyncio
async def test_cancel_request_accepts_a_delayed_start_before_agent_ack(client, db_session):
    case_id, version_id = _create_case_version(client)
    agent = _register_agent(client)
    queued, _ = _queue_and_claim(client, agent, case_id, version_id, client_run_key="cancel-delayed-start")
    assert client.post(f"/api/ui-automation/runs/{queued['id']}/cancel").status_code == 200
    response = client.post(
        f"/api/ui-automation/agents/{agent['id']}/runs/{queued['id']}/events",
        headers={"X-TestMaster-Agent-Token": agent["bootstrap_token"]},
        json={
            "events": [
                {"sequence": 1, "type": "run:start", "totalSteps": 1},
                {"sequence": 2, "type": "run:finish", "status": "cancelled"},
            ]
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"
