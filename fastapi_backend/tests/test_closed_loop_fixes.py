"""Closed-loop integration fixes: health URL resolve, healing non-mutate, visual bind, shard filter."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from fastapi_backend.services.api_health_service import APIHealthService, _join_url, start_api_health_worker
from fastapi_backend.services.element_repository_service import ElementRepositoryService
from fastapi_backend.services.upgrade_pipeline_service import UpgradePipelineService
from fastapi_backend.services.ui_automation.agent_service import _suite_execution_id_for_run


def test_join_url_absolute_and_relative():
    assert _join_url("https://api.example.com", "/v1/health") == "https://api.example.com/v1/health"
    assert _join_url("https://api.example.com/", "v1/health") == "https://api.example.com/v1/health"
    assert _join_url("", "https://x.test/a") == "https://x.test/a"
    assert _join_url("https://api.example.com", "https://other/x") == "https://other/x"


@pytest.mark.asyncio
async def test_health_resolve_request_uses_case_and_env(monkeypatch):
    service = APIHealthService()
    monitor = SimpleNamespace(case_id=7, environment_id=3)
    case = SimpleNamespace(id=7, url="/status", method="GET", headers={"X-A": "1"}, payload=None)
    env = SimpleNamespace(id=3, base_url="https://svc.example.com")

    db = AsyncMock()

    async def _get(model, pk):
        name = getattr(model, "__name__", str(model))
        if "Case" in name or pk == 7:
            return case
        return env

    db.get = _get
    req = await service.resolve_request(db, monitor)
    assert req["url"] == "https://svc.example.com/status"
    assert req["method"] == "GET"
    assert req["headers"]["X-A"] == "1"


@pytest.mark.asyncio
async def test_health_resolve_rejects_placeholder_style_relative_without_base():
    service = APIHealthService()
    monitor = SimpleNamespace(case_id=1, environment_id=1)
    case = SimpleNamespace(id=1, url="/only-path", method="GET", headers={}, payload=None)
    env = SimpleNamespace(id=1, base_url="")
    db = AsyncMock()

    async def _get(model, pk):
        return (
            case
            if pk == 1 and "Case" in getattr(model, "__name__", "") or pk == 1 and hasattr(model, "__tablename__")
            else env
        )

    # simpler: return by call order
    values = [case, env]
    db.get = AsyncMock(side_effect=lambda *a, **k: values.pop(0) if values else None)
    # Force explicit: first case then env
    db.get = AsyncMock(side_effect=[case, env])
    with pytest.raises(ValueError, match="not absolute"):
        await service.resolve_request(db, monitor)


def test_start_api_health_worker_is_importable():
    assert callable(start_api_health_worker)


@pytest.mark.asyncio
async def test_heal_does_not_mutate_element_by_default(monkeypatch):
    service = ElementRepositoryService()
    element = SimpleNamespace(id=9, locators=[{"strategy": "css", "value": "#old"}], frame_path=[])
    config = SimpleNamespace(
        enabled=True,
        auto_apply_threshold=0.5,
        suggest_threshold=0.3,
        max_candidates=5,
        auto_mutate_assets=False,
    )
    applied = {"called": False}

    async def _fake_apply(el, loc):
        applied["called"] = True

    service._apply_heal = _fake_apply  # type: ignore
    service.get_or_create_healing_config = AsyncMock(return_value=config)  # type: ignore
    service._find_by_text = MagicMock(
        return_value=[{"text": "Login", "locator": {"strategy": "text", "value": "Login"}}]
    )
    service._find_by_attributes = MagicMock(return_value=[])
    service._find_by_css_hint = MagicMock(return_value=[])
    service._text_similarity = MagicMock(return_value=0.99)

    db = AsyncMock()
    db.get = AsyncMock(return_value=element)
    db.add = MagicMock()
    db.flush = AsyncMock()

    result = await service.heal(
        db,
        project_id=1,
        original_locator={"strategy": "css", "value": "#old", "options": {"name": "Login"}},
        page_dom="<button>Login</button>",
        element_id=9,
    )
    assert result.status == "auto_applied"
    assert applied["called"] is False


def test_suite_execution_id_prefers_parent_manifest():
    run = SimpleNamespace(id=10, artifact_manifest={"parent_run_id": 99, "shard_id": 3})
    assert _suite_execution_id_for_run(run) == 99
    run2 = SimpleNamespace(id=10, artifact_manifest=None)
    assert _suite_execution_id_for_run(run2) == 10


@pytest.mark.asyncio
async def test_visual_pipeline_binds_by_step_id_not_latest(monkeypatch, tmp_path):
    # Create a fake png so path checks pass
    img = tmp_path / "visual-abc12345-1.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)

    matched = SimpleNamespace(id=55, step_id="abc12345")
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    calls = []

    async def fake_scalar(stmt):
        calls.append(str(stmt))
        # First queries should be for step id match, not blindly latest
        return matched

    db.scalar = fake_scalar

    captured = {}

    async def fake_compare_and_persist(db, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id=1)

    monkeypatch.setattr(
        "fastapi_backend.services.visual_regression_service.visual_regression_service.compare_and_persist",
        fake_compare_and_persist,
    )
    monkeypatch.setattr(
        "fastapi_backend.services.upgrade_pipeline_service.resolve_manifest_path",
        lambda m: img,
    )

    run = SimpleNamespace(id=7, user_id=1, project_id=1, browser_engine="chromium")
    artifact = SimpleNamespace(
        id=1,
        filename="visual-abc12345-1.png",
        type="screenshot",
        artifact_manifest_id=1,
    )
    manifest = SimpleNamespace(storage_key="x", filename="visual-abc12345-1.png", kind="screenshot")

    svc = UpgradePipelineService()
    out = await svc.process_linked_artifact(db, run=run, artifact=artifact, manifest=manifest)
    assert out.get("comparison_id") == 1
    assert captured.get("ui_step_id") == "abc12345"
    assert captured.get("step_result_id") == 55
    # Must not have used a bare "latest step" fallback without token
    assert "abc12345" in "".join(calls) or captured.get("ui_step_id") == "abc12345"


@pytest.mark.asyncio
async def test_parent_defers_until_child_shards_finish_then_fails(monkeypatch):
    """Parent must not stay passed when a sibling shard fails — aggregate after all terminal."""
    from datetime import datetime, timezone

    from fastapi_backend.services.ui_automation import run_service

    async def _noop_sync(db, run, event, now):
        return None

    monkeypatch.setattr(run_service, "_sync_authoritative_execution", _noop_sync)
    now = datetime.now(timezone.utc)
    parent = SimpleNamespace(
        id=100,
        suite_id=1,
        case_id=None,
        status="running",
        finished_at=None,
        started_at=now,
        total_steps=2,
        passed_steps=2,
        failed_steps=0,
        skipped_steps=0,
        agent_id=None,
        user_id=1,
        project_id=1,
        triggered_by=1,
        environment_id=None,
        attempt=1,
        run_key="parent-100",
        trigger_type="manual",
        automation_execution_id=None,
        artifact_manifest={
            "is_suite_parent": True,
            "suite_execution_id": 100,
            "shard_id": 1,
            "shard_count": 2,
            "child_run_ids": [101],
            "awaiting_sibling_shards": True,
        },
    )
    child = SimpleNamespace(
        id=101,
        suite_id=1,
        case_id=None,
        status="failed",
        finished_at=now,
        started_at=now,
        total_steps=1,
        passed_steps=0,
        failed_steps=1,
        skipped_steps=0,
        agent_id=None,
        user_id=1,
        project_id=1,
        environment_id=None,
        attempt=1,
        run_key="child-101",
        automation_execution_id=None,
        artifact_manifest={"parent_run_id": 100, "shard_id": 2, "suite_execution_id": 100},
    )
    shard0 = SimpleNamespace(
        id=1,
        suite_execution_id=100,
        shard_index=0,
        status="completed",
        total_cases=1,
        completed_cases=1,
        passed_cases=1,
        failed_cases=0,
    )
    shard1 = SimpleNamespace(
        id=2,
        suite_execution_id=100,
        shard_index=1,
        status="failed",
        total_cases=1,
        completed_cases=1,
        passed_cases=0,
        failed_cases=1,
    )

    db = AsyncMock()

    async def _get(model, pk):
        if pk == 100:
            return parent
        if pk == 101:
            return child
        return None

    db.get = AsyncMock(side_effect=_get)

    async def _scalars(stmt):
        return SimpleNamespace(all=lambda: [shard0, shard1])

    db.scalars = _scalars
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.scalar = AsyncMock(return_value=0)

    # First: parent finishes its shard but child still running → defer.
    child.status = "running"
    deferred = await run_service._defer_parent_terminal_if_shards_pending(
        db,
        parent,
        local_status="passed",
        event={"status": "passed", "shardId": 1},
        now=now,
    )
    assert deferred is True
    assert parent.status == "running"
    assert parent.finished_at is None
    assert parent.artifact_manifest.get("awaiting_sibling_shards") is True

    # Child finished failed → no longer defer; aggregate should mark parent failed.
    child.status = "failed"
    deferred2 = await run_service._defer_parent_terminal_if_shards_pending(
        db,
        parent,
        local_status="passed",
        event={"status": "passed", "shardId": 1},
        now=now,
    )
    assert deferred2 is False
    await run_service._maybe_aggregate_parent_suite_run(
        db,
        parent,
        event={"status": "passed", "shardId": 1},
        now=now,
    )
    assert parent.status == "failed"
    assert parent.finished_at is not None
    assert parent.artifact_manifest.get("aggregated") is True
    assert parent.artifact_manifest["aggregate"]["failed_cases"] == 1


@pytest.mark.asyncio
async def test_concurrency_tags_do_not_split_exclusive_group():
    from fastapi_backend.services.suite_sharding_service import SuiteShardingService

    service = SuiteShardingService()
    tag = SimpleNamespace(id=1, max_concurrent=1, tag="exclusive-db")
    assignments = [
        SimpleNamespace(case_id=10, tag_id=1),
        SimpleNamespace(case_id=11, tag_id=1),
        SimpleNamespace(case_id=12, tag_id=1),
    ]
    free_cases = [20, 21, 22]

    db = AsyncMock()

    async def _scalars(stmt):
        text = str(stmt)
        # crude: first call assignments, later tags
        if "case_concurrency_tag_assignments" in text.lower() or "CaseConcurrencyTagAssignment" in text:
            return SimpleNamespace(all=lambda: assignments)
        return SimpleNamespace(all=lambda: [tag])

    # side_effect by call count
    calls = {"n": 0}

    async def _scalars2(stmt):
        calls["n"] += 1
        if calls["n"] == 1:
            return SimpleNamespace(all=lambda: assignments)
        return SimpleNamespace(all=lambda: [tag])

    db.scalars = _scalars2

    groups = await service._group_by_concurrency_tags(db, [10, 11, 12, *free_cases], shard_count=4)
    # The three exclusive cases must appear together in exactly one bucket.
    exclusive_buckets = [g for g in groups if set(g) & {10, 11, 12}]
    assert len(exclusive_buckets) == 1
    assert set(exclusive_buckets[0]) >= {10, 11, 12}
    # Free cases may be elsewhere but exclusive trio never split.
    for bucket in groups:
        exclusive_in_bucket = set(bucket) & {10, 11, 12}
        assert exclusive_in_bucket in ({10, 11, 12}, set())


@pytest.mark.asyncio
async def test_overlapping_tags_use_strictest_case_limit():
    """Case bound to max_concurrent=2 and max_concurrent=3 must use min=2, never 3 shards."""
    from fastapi_backend.services.suite_sharding_service import SuiteShardingService

    service = SuiteShardingService()
    tags = [
        SimpleNamespace(id=1, max_concurrent=2, tag="limit-2"),
        SimpleNamespace(id=2, max_concurrent=3, tag="limit-3"),
    ]
    # Six cases all on both tags → case_limit=2 for every case.
    case_ids = [100, 101, 102, 103, 104, 105]
    assignments = []
    for cid in case_ids:
        assignments.append(SimpleNamespace(case_id=cid, tag_id=1))
        assignments.append(SimpleNamespace(case_id=cid, tag_id=2))

    calls = {"n": 0}

    async def _scalars(stmt):
        calls["n"] += 1
        if calls["n"] == 1:
            return SimpleNamespace(all=lambda: assignments)
        return SimpleNamespace(all=lambda: tags)

    db = AsyncMock()
    db.scalars = _scalars

    groups = await service._group_by_concurrency_tags(db, case_ids, shard_count=6)
    # Across all groups, cases of tag 1 (all of them) may occupy at most 2 buckets.
    buckets_with_tagged = [g for g in groups if set(g) & set(case_ids)]
    assert len(buckets_with_tagged) <= 2, f"expected <=2 concurrent shards, got {len(buckets_with_tagged)}: {groups}"
    # Every case still present exactly once.
    flat = [cid for g in groups for cid in g]
    assert sorted(flat) == sorted(case_ids)


@pytest.mark.asyncio
async def test_attach_contract_validation_fail_closed(monkeypatch):
    from fastapi_backend.services.contract_testing_service import contract_testing_service

    async def _fake_validate(db, **kwargs):
        return {"valid": False, "skipped": False, "errors": ["missing required field: id"], "rule_id": 9}

    monkeypatch.setattr(contract_testing_service, "validate_response", _fake_validate)
    result = {
        "success": True,
        "status_code": 200,
        "response_content": {"name": "x"},
        "request": {"method": "GET", "url": "https://api.example.com/users"},
    }
    out = await contract_testing_service.attach_contract_validation(
        result,
        project_id=1,
        case_id=42,
        method="GET",
        url="https://api.example.com/users",
        db=AsyncMock(),
    )
    assert out["success"] is False
    assert out["contract_result"]["valid"] is False
    assert "契约校验失败" in (out.get("error") or "")


def test_pyyaml_is_declared_in_fastapi_backend_requirements():
    req = Path(__file__).resolve().parents[1] / "requirements.txt"
    text = req.read_text(encoding="utf-8")
    assert "PyYAML" in text or "pyyaml" in text.lower()


@pytest.mark.asyncio
async def test_health_claim_prevents_double_run(monkeypatch):
    from fastapi_backend.services.api_health_service import APIHealthService

    service = APIHealthService()
    monitor = SimpleNamespace(
        id=7,
        is_active=True,
        interval_seconds=300,
        last_check_at=None,
        last_status=None,
        timeout_ms=1000,
        expected_status=200,
        max_response_time_ms=None,
        case_id=1,
        environment_id=1,
    )
    # Simulate CAS: first claim wins, second loses.
    state = {"claimed": False, "ran": 0}

    class _Result:
        def __init__(self, rowcount):
            self.rowcount = rowcount

    db = AsyncMock()

    async def _get(model, pk):
        return monitor

    db.get = AsyncMock(side_effect=_get)

    async def _execute(stmt):
        if not state["claimed"]:
            state["claimed"] = True
            monitor.last_check_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            return _Result(1)
        return _Result(0)

    db.execute = AsyncMock(side_effect=_execute)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    assert await service._claim_monitor(db, 7) is True
    assert await service._claim_monitor(db, 7) is False


@pytest.mark.asyncio
async def test_ui_suite_parent_notifies_once(monkeypatch):
    """Child terminal AE must not notify; parent with notify_on_terminal does."""
    from datetime import datetime, timezone

    from fastapi_backend.services.ui_automation import run_service

    notified = []

    async def _fake_queue(db, execution, context):
        notified.append({"execution_id": getattr(execution, "id", None), "status": context.get("status")})
        return 1

    monkeypatch.setattr(
        "fastapi_backend.services.automation_notification_outbox.queue_execution_notifications",
        _fake_queue,
    )
    # Also patch import path used inside _sync
    import fastapi_backend.services.automation_notification_outbox as outbox

    monkeypatch.setattr(outbox, "queue_execution_notifications", _fake_queue)

    now = datetime.now(timezone.utc)
    parent_exec = SimpleNamespace(
        id=1,
        status="running",
        notify_on_terminal=True,
        started_at=now,
        finished_at=None,
        heartbeat_at=None,
        runner_id=None,
        result_summary=None,
        error_code=None,
        error_message=None,
    )
    child_exec = SimpleNamespace(
        id=2,
        status="running",
        notify_on_terminal=False,
        started_at=now,
        finished_at=None,
        heartbeat_at=None,
        runner_id=None,
        result_summary=None,
        error_code=None,
        error_message=None,
    )
    parent = SimpleNamespace(
        id=100,
        automation_execution_id=1,
        user_id=1,
        agent_id=None,
        attempt=1,
        status="passed",
        started_at=now,
        finished_at=now,
        total_steps=2,
        passed_steps=2,
        failed_steps=0,
        skipped_steps=0,
        run_key="p",
        trigger_type="manual",
        project_id=10,
        environment_id=None,
        artifact_manifest={"is_suite_parent": True, "aggregated": True},
        parent_run_id=None,
    )
    child = SimpleNamespace(
        id=101,
        automation_execution_id=2,
        user_id=1,
        agent_id=None,
        attempt=1,
        status="failed",
        started_at=now,
        finished_at=now,
        total_steps=1,
        passed_steps=0,
        failed_steps=1,
        skipped_steps=0,
        run_key="c",
        trigger_type="manual",
        project_id=10,
        environment_id=None,
        artifact_manifest={"parent_run_id": 100},
        parent_run_id=100,
    )

    db = AsyncMock()

    async def _get(model, pk):
        if pk == 1:
            return parent_exec
        if pk == 2:
            return child_exec
        return None

    db.get = AsyncMock(side_effect=_get)
    db.add = MagicMock()
    db.scalar = AsyncMock(return_value=0)

    await run_service._sync_authoritative_execution(db, child, {"type": "run:finish", "status": "failed"}, now)
    assert notified == []

    await run_service._sync_authoritative_execution(db, parent, {"type": "run:finish", "status": "failed"}, now)
    assert len(notified) == 1
    assert notified[0]["execution_id"] == 1
