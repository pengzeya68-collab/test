import hashlib

import pytest
from sqlalchemy import select
from types import SimpleNamespace

from fastapi_backend.deps.auth import get_current_active_user, get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import AutomationExecution, ExecutionEvent
from fastapi_backend.models.ui_automation import UIArtifact, UIRun, UIStepResult


@pytest.fixture(autouse=True)
def enable_ui_automation():
    from fastapi_backend.core.config import settings

    original = settings.UI_AUTOMATION_ENABLED
    settings.UI_AUTOMATION_ENABLED = True
    yield
    settings.UI_AUTOMATION_ENABLED = original


@pytest.fixture(autouse=True)
def override_current_user():
    async def _override_current_user():
        return SimpleNamespace(
            id=1, username="tester", is_active=True, is_admin=True, is_super_admin=True, role_id=None
        )

    app.dependency_overrides[get_current_active_user] = _override_current_user
    app.dependency_overrides[get_current_user] = _override_current_user
    yield
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)


def _create_case(client, name="Login case"):
    response = client.post("/api/ui-automation/cases", json={"name": name, "base_url": "https://example.com"})
    assert response.status_code == 200, response.text
    return response.json()


def _save_steps(client, case_id: int):
    response = client.put(
        f"/api/ui-automation/cases/{case_id}/steps",
        json={
            "steps": [
                {"id": "step-1", "order": 10, "type": "goto", "input": {"url": "https://example.com"}},
                {"id": "step-2", "order": 20, "type": "click", "locator": {"strategy": "css", "value": "#submit"}},
            ]
        },
    )
    assert response.status_code == 200, response.text


def _upload_shared_artifact(
    client,
    run: dict,
    content: bytes,
    *,
    kind: str = "screenshot",
    filename: str = "proof.png",
    content_type: str = "image/png",
) -> dict:
    created = client.post(
        "/api/auto-test/artifacts/upload-sessions",
        json={
            "execution_id": run["execution_id"],
            "kind": kind,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    )
    assert created.status_code == 201, created.text
    session = created.json()
    uploaded = client.put(
        session["chunk_endpoint"],
        content=content,
        headers={"Content-Range": f"bytes 0-{len(content) - 1}/{len(content)}"},
    )
    assert uploaded.status_code == 204, uploaded.text
    completed = client.post(f"/api/auto-test/artifacts/upload-sessions/{session['upload_id']}/complete")
    assert completed.status_code == 200, completed.text
    linked = client.post(
        f"/api/ui-automation/runs/{run['id']}/artifacts/link",
        json={"artifact_manifest_id": completed.json()["artifact_id"]},
    )
    assert linked.status_code == 200, linked.text
    return {**linked.json(), "manifest_id": completed.json()["artifact_id"]}


@pytest.mark.asyncio
async def test_invalid_step_type_is_rejected(client):
    case = _create_case(client)
    response = client.put(
        f"/api/ui-automation/cases/{case['id']}/steps",
        json={"steps": [{"id": "bad-step", "order": 10, "type": "totally_unknown"}]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_step_ids_are_remapped_when_another_case_already_uses_them(client):
    first = _create_case(client, name="First reusable flow")
    second = _create_case(client, name="Second reusable flow")
    payload = {"steps": [{"id": "shared-open", "order": 10, "type": "goto", "input": {"url": "https://example.com"}}]}

    first_saved = client.put(f"/api/ui-automation/cases/{first['id']}/steps", json=payload)
    second_saved = client.put(f"/api/ui-automation/cases/{second['id']}/steps", json=payload)

    assert first_saved.status_code == 200, first_saved.text
    assert second_saved.status_code == 200, second_saved.text
    assert first_saved.json()["steps"][0]["id"] == "shared-open"
    assert second_saved.json()["steps"][0]["id"] != "shared-open"


@pytest.mark.asyncio
async def test_create_run_is_idempotent_by_client_run_key(client):
    case = _create_case(client, name="Idempotent run case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()

    payload = {
        "case_id": case["id"],
        "case_version_id": version["id"],
        "client_run_key": "run-key-001",
        "trigger_type": "manual",
    }
    first = client.post("/api/ui-automation/runs", json=payload)
    second = client.post("/api/ui-automation/runs", json=payload)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["run_key"] == second.json()["run_key"]


@pytest.mark.asyncio
async def test_run_lifecycle_and_results(client, db_session):
    case = _create_case(client)
    _save_steps(client, case["id"])

    version_response = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={"change_summary": "ready"})
    assert version_response.status_code == 200, version_response.text
    version = version_response.json()

    run_response = client.post(
        "/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}
    )
    assert run_response.status_code == 200, run_response.text
    run = run_response.json()
    assert run["status"] == "queued"
    assert run["total_steps"] == 2

    events_response = client.post(
        f"/api/ui-automation/runs/{run['id']}/events",
        json={
            "events": [
                {"sequence": 1, "type": "run:start", "totalSteps": 2},
                {"sequence": 2, "type": "step:start", "stepId": "step-1", "stepName": "Open", "stepType": "goto"},
                {"sequence": 3, "type": "step:pass", "stepId": "step-1", "durationMs": 120},
                {"sequence": 4, "type": "step:start", "stepId": "step-2", "stepName": "Submit", "stepType": "click"},
                {
                    "sequence": 5,
                    "type": "step:fail",
                    "stepId": "step-2",
                    "durationMs": 230,
                    "error": "locator not found",
                },
                {"sequence": 6, "type": "run:finish", "status": "failed", "passedSteps": 1, "failedSteps": 1},
            ]
        },
    )
    assert events_response.status_code == 200, events_response.text
    assert events_response.json()["accepted"] == 6
    assert events_response.json()["status"] == "failed"

    duplicate_response = client.post(
        f"/api/ui-automation/runs/{run['id']}/events",
        json={
            "events": [{"sequence": 6, "type": "run:finish", "status": "failed", "passedSteps": 1, "failedSteps": 1}]
        },
    )
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["ignored"] == 1

    run_detail = client.get(f"/api/ui-automation/runs/{run['id']}")
    assert run_detail.status_code == 200
    assert run_detail.json()["status"] == "failed"
    assert run_detail.json()["passed_steps"] == 1
    assert run_detail.json()["failed_steps"] == 1

    step_results = client.get(f"/api/ui-automation/runs/{run['id']}/step-results")
    assert step_results.status_code == 200
    assert step_results.json()["total"] == 2
    statuses = {item["step_id"]: item["status"] for item in step_results.json()["items"]}
    assert statuses["step-1"] == "passed"
    assert statuses["step-2"] == "failed"

    db_run = await db_session.get(UIRun, run["id"])
    assert db_run is not None
    assert db_run.artifact_manifest["_last_sequence"] == 6
    assert run["execution_id"]
    execution = await db_session.get(AutomationExecution, db_run.automation_execution_id)
    assert execution.status == "failed"
    events = list(
        (await db_session.scalars(select(ExecutionEvent).where(ExecutionEvent.execution_id == execution.id))).all()
    )
    assert len(events) == 7


@pytest.mark.asyncio
async def test_artifact_storage_path_is_server_controlled(client, db_session):
    case = _create_case(client, name="Artifacts case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    run = client.post("/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}).json()

    artifact_response = client.post(
        f"/api/ui-automation/runs/{run['id']}/artifacts",
        json={"type": "screenshot", "filename": "..\\..\\danger.png", "mime_type": "image/png", "size_bytes": 1234},
    )
    assert artifact_response.status_code == 200, artifact_response.text
    artifact = artifact_response.json()
    assert artifact["filename"] == "danger.png"
    assert ".." not in artifact["storage_path"]
    assert artifact["storage_path"].startswith("ui_automation/artifacts/")

    artifact_list = client.get(f"/api/ui-automation/runs/{run['id']}/artifacts")
    assert artifact_list.status_code == 200
    assert artifact_list.json()["total"] == 1

    db_artifact = await db_session.get(UIArtifact, artifact["id"])
    assert db_artifact is not None


@pytest.mark.asyncio
async def test_group_and_case_isolation_validation(client):
    create_group = client.post("/api/ui-automation/groups", json={"name": "Owned group"})
    assert create_group.status_code == 200
    group_id = create_group.json()["id"]

    case_response = client.post("/api/ui-automation/cases", json={"name": "Grouped", "group_id": group_id})
    assert case_response.status_code == 200

    invalid_group = client.post("/api/ui-automation/cases", json={"name": "Bad group", "group_id": 999999})
    assert invalid_group.status_code == 422


@pytest.mark.asyncio
async def test_ui_run_links_resumable_shared_artifact(client):
    case = _create_case(client, name="Upload artifact case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    run = client.post("/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}).json()

    artifact = _upload_shared_artifact(client, run, b"hello")
    assert artifact["storage_type"] == "shared"
    assert artifact["artifact_manifest_id"] == artifact["manifest_id"]
    content = client.get(f"/api/auto-test/artifacts/{artifact['manifest_id']}/content")
    assert content.status_code == 200, content.text
    assert content.content == b"hello"


@pytest.mark.asyncio
async def test_legacy_base64_artifact_endpoint_is_unavailable(client):
    case = _create_case(client, name="Bad artifact case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    run = client.post("/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}).json()

    response = client.post(
        f"/api/ui-automation/runs/{run['id']}/artifacts/upload",
        json={
            "type": "screenshot",
            "filename": "broken.png",
            "mime_type": "image/png",
            "content_base64": "%%%not-base64%%%",
        },
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_shared_artifact_upload_rejects_oversized_payload(client):
    case = _create_case(client, name="Large artifact case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    run = client.post("/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}).json()
    response = client.post(
        "/api/auto-test/artifacts/upload-sessions",
        json={
            "execution_id": run["execution_id"],
            "kind": "screenshot",
            "filename": "too-large.png",
            "size_bytes": 100 * 1024 * 1024 + 1,
            "sha256": "a" * 64,
        },
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_console_and_network_diagnostics_are_persisted(client, db_session):
    case = _create_case(client, name="Diagnostics report case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    run = client.post("/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}).json()

    response = client.post(
        f"/api/ui-automation/runs/{run['id']}/events",
        json={
            "events": [
                {"sequence": 1, "type": "run:start", "totalSteps": 2},
                {
                    "sequence": 2,
                    "type": "console",
                    "level": "error",
                    "text": "frontend failed",
                    "url": "https://app.example/page",
                },
                {
                    "sequence": 3,
                    "type": "network",
                    "method": "POST",
                    "url": "https://api.example/order",
                    "httpStatus": 503,
                },
                {
                    "sequence": 4,
                    "type": "console",
                    "level": "error",
                    "text": '{"token":"real-token","message":"visible"}',
                    "url": "https://app.example/page?access_token=top-secret",
                },
            ]
        },
    )
    assert response.status_code == 200, response.text
    db_session.expire_all()
    stored = await db_session.get(UIRun, run["id"])
    diagnostics = stored.artifact_manifest["diagnostics"]
    assert diagnostics[0]["text"] == "frontend failed"
    assert diagnostics[1]["method"] == "POST"
    assert diagnostics[1]["http_status"] == 503
    assert "real-token" not in diagnostics[2]["text"]
    assert "top-secret" not in diagnostics[2]["url"]
    assert "[REDACTED]" in diagnostics[2]["text"]


@pytest.mark.asyncio
async def test_artifact_content_can_be_read_only_through_owning_run(client):
    case = _create_case(client, name="Readable artifact case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    run = client.post("/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}).json()
    artifact = _upload_shared_artifact(
        client, run, b"zip-content", kind="trace", filename="trace.zip", content_type="application/zip"
    )

    content = client.get(f"/api/ui-automation/runs/{run['id']}/artifacts/{artifact['id']}/content")
    assert content.status_code == 200, content.text
    assert content.content == b"zip-content"

    other_case = _create_case(client, name="Other artifact run")
    other_steps = client.put(
        f"/api/ui-automation/cases/{other_case['id']}/steps",
        json={"steps": [{"id": "other-step-1", "order": 10, "type": "goto", "input": {"url": "https://example.com"}}]},
    )
    assert other_steps.status_code == 200, other_steps.text
    other_version = client.post(f"/api/ui-automation/cases/{other_case['id']}/versions", json={}).json()
    other_run = client.post(
        "/api/ui-automation/runs", json={"case_id": other_case["id"], "case_version_id": other_version["id"]}
    ).json()
    denied = client.get(f"/api/ui-automation/runs/{other_run['id']}/artifacts/{artifact['id']}/content")
    assert denied.status_code == 404


@pytest.mark.asyncio
async def test_agent_registration_authentication_and_claim(client):
    case = _create_case(client, name="Agent claim case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    registered = client.post(
        "/api/ui-automation/agents",
        json={
            "name": "Windows runner",
            "hostname": "qa-win-01",
            "max_parallel": 1,
            "capabilities": {"chromium": True},
        },
    )
    assert registered.status_code == 200, registered.text
    agent = registered.json()
    assert agent["bootstrap_token"]
    assert "agent_token_hash" not in agent

    queued = client.post(
        "/api/ui-automation/runs",
        json={
            "case_id": case["id"],
            "case_version_id": version["id"],
            "agent_id": agent["id"],
            "trigger_type": "scheduled",
            "client_run_key": "agent-claim-run",
        },
    )
    assert queued.status_code == 200, queued.text
    assert queued.json()["status"] == "waiting_for_agent"

    denied = client.post(f"/api/ui-automation/agents/{agent['id']}/claim")
    assert denied.status_code == 401
    claimed = client.post(
        f"/api/ui-automation/agents/{agent['id']}/claim",
        headers={"X-TestMaster-Agent-Token": agent["bootstrap_token"]},
    )
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["run"]["id"] == queued.json()["id"]
    assert claimed.json()["run"]["status"] == "assigned"
    assert claimed.json()["plan"]["kind"] == "case"


@pytest.mark.asyncio
async def test_failure_report_and_annotation_layer_use_shared_artifacts(client):
    case = _create_case(client, name="Failure report case")
    _save_steps(client, case["id"])
    version = client.post(f"/api/ui-automation/cases/{case['id']}/versions", json={}).json()
    run = client.post("/api/ui-automation/runs", json={"case_id": case["id"], "case_version_id": version["id"]}).json()
    events = client.post(
        f"/api/ui-automation/runs/{run['id']}/events",
        json={
            "events": [
                {"sequence": 1, "type": "run:start", "totalSteps": 2},
                {
                    "sequence": 2,
                    "type": "step:fail",
                    "stepId": "step-1",
                    "durationMs": 30,
                    "error": "expected confirmation",
                },
                {"sequence": 3, "type": "run:finish", "status": "failed", "passedSteps": 0, "failedSteps": 1},
            ]
        },
    )
    assert events.status_code == 200, events.text
    artifact = _upload_shared_artifact(client, run, b"png-bytes")
    report = client.get(f"/api/ui-automation/runs/{run['id']}/defect-report")
    assert report.status_code == 200, report.text
    assert report.json()["failed_steps"][0]["error_message"] == "expected confirmation"
    assert report.json()["artifacts"][0]["artifact_manifest_id"] == artifact["manifest_id"]
    assert report.json()["timeline"][-1]["type"] == "ui_run_finish"

    saved = client.put(
        f"/api/ui-automation/artifacts/{artifact['manifest_id']}/annotations",
        json={
            "annotations": [{"type": "rectangle", "x": 1, "y": 2, "width": 3, "height": 4, "note": "unexpected state"}]
        },
    )
    assert saved.status_code == 200, saved.text
    loaded = client.get(f"/api/ui-automation/artifacts/{artifact['manifest_id']}/annotations")
    assert loaded.status_code == 200
    assert loaded.json()["annotations"][0]["note"] == "unexpected state"
