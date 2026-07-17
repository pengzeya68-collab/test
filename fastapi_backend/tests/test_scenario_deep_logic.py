import httpx
import pytest
from unittest.mock import AsyncMock
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_backend.services.autotest_scenario_runner import ScenarioExecutionEngine
import fastapi_backend.services.autotest_scenario_runner as scenario_runner
from fastapi_backend.core.database import Base
from fastapi_backend.models.autotest import AutoTestCase, AutoTestEnvironment, AutoTestScenario, AutoTestScenarioStep


def make_step(step_id, order, step_type="api_request", config=None):
    return {
        "id": step_id,
        "step_order": order,
        "step_type": step_type,
        "step_config": config or {},
        "api_case_id": step_id,
    }


@pytest.mark.asyncio
async def test_group_failure_propagates_to_parent(monkeypatch):
    engine = ScenarioExecutionEngine(1)
    engine.fail_fast = False
    engine.failed_encountered = False
    child = make_step(20, 200)
    group = make_step(10, 100, "group", {"reference_mode": "id", "children": [20]})

    async def fail_child(*_args):
        return {"step_id": 20, "step_order": 200, "success": False, "error": "boom"}

    monkeypatch.setattr(engine, "_dispatch_step", fail_child)
    result = await engine._execute_group(group, [group, child], 0)

    assert result["success"] is False
    assert engine.failed_encountered is True
    assert engine.step_results[0]["status"] == "failed"


@pytest.mark.asyncio
async def test_fail_fast_loop_stops_after_first_failed_iteration(monkeypatch):
    engine = ScenarioExecutionEngine(1)
    engine.fail_fast = True
    engine.failed_encountered = False
    child = make_step(20, 200)
    loop = make_step(10, 100, "for_loop", {
        "reference_mode": "id", "count": 5, "var_name": "i", "body": [20]
    })
    calls = 0

    async def fail_child(*_args):
        nonlocal calls
        calls += 1
        return {"step_id": 20, "step_order": 200, "success": False, "error": "boom"}

    monkeypatch.setattr(engine, "_dispatch_step", fail_child)
    result = await engine._execute_for(loop, [loop, child], 0)

    assert result["iterations"] == 1
    assert result["success"] is False
    assert calls == 1


def test_stable_id_reference_survives_reorder():
    engine = ScenarioExecutionEngine(1)
    target = make_step(42, 999)
    config = {"reference_mode": "id", "children": [42]}
    assert engine._find_referenced_step(42, [target], config) is target


def test_condition_supports_placeholder_and_nested_variable_paths():
    engine = ScenarioExecutionEngine(1)
    engine.context_vars = {"token": "abc", "user": {"level": 3}}
    assert engine._evaluate_condition({"variable": "{{token}}", "operator": "equals", "value": "abc"})
    assert engine._evaluate_condition({"variable": "user.level", "operator": ">", "value": 2})


@pytest.mark.asyncio
async def test_step_variable_override_does_not_leak_to_following_steps():
    engine = ScenarioExecutionEngine(1)
    engine.context_vars = {"scope": "base"}
    engine.session_vars = {}

    async def handler(request):
        return httpx.Response(200, json={"path": request.url.path})

    engine._shared_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    step = {
        **make_step(1, 1),
        "api_case_name": "temporary override",
        "api_case_method": "GET",
        "api_case_url": "https://example.test/{{scope}}",
        "api_case_headers": {},
        "api_case_params": {},
        "api_case_body": None,
        "api_case_body_type": "none",
        "api_case_assert_rules": [],
        "api_case_extractors": [],
        "variable_overrides": {"variables": {"scope": "temporary"}},
    }
    try:
        result = await engine._execute_api_request(step)
    finally:
        await engine._shared_client.aclose()
        engine._shared_client = None

    assert result["success"] is True
    assert result["url"].endswith("/temporary")
    assert engine.context_vars["scope"] == "base"


@pytest.mark.asyncio
async def test_scenario_step_uses_saved_request_auth_and_runtime_variables():
    engine = ScenarioExecutionEngine(1)
    engine.context_vars = {"token": "scenario-token"}
    engine.session_vars = {}
    captured = {}

    async def handler(request):
        captured["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={"ok": True})

    engine._shared_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    step = {
        **make_step(1, 1),
        "api_case_name": "authenticated request",
        "api_case_method": "GET",
        "api_case_url": "https://example.test/profile",
        "api_case_headers": {},
        "api_case_params": {},
        "api_case_body": None,
        "api_case_body_type": "none",
        "api_case_assert_rules": [],
        "api_case_extractors": [],
        "api_case_request_config": {"auth": {"type": "bearer", "token": "{{token}}"}},
    }
    try:
        result = await engine._execute_api_request(step)
    finally:
        await engine._shared_client.aclose()

    assert result["success"] is True
    assert captured["authorization"] == "Bearer scenario-token"


@pytest.mark.asyncio
async def test_extracted_variables_are_run_scoped_by_default(monkeypatch):
    persist = AsyncMock(return_value=True)
    monkeypatch.setattr(scenario_runner, "save_variables_to_db", persist)
    engine = ScenarioExecutionEngine(1, user_id=7)
    response = {"json": {"token": "run-token"}, "body": '{"token":"run-token"}', "headers": {}}

    extracted = await engine._extract_variables([
        {"variableName": "token", "extractorType": "jsonpath", "expression": "$.token"}
    ], response)

    assert extracted["token"] == "run-token"
    assert engine.context_vars["token"] == "run-token"
    persist.assert_not_awaited()


@pytest.mark.asyncio
async def test_extractor_can_explicitly_persist_global_value(monkeypatch):
    persist = AsyncMock(return_value=True)
    monkeypatch.setattr(scenario_runner, "save_variables_to_db", persist)
    engine = ScenarioExecutionEngine(1, user_id=7)
    response = {"json": {"tenant": "acme"}, "body": '{"tenant":"acme"}', "headers": {}}

    await engine._extract_variables([
        {"variableName": "tenant", "extractorType": "jsonpath", "expression": "$.tenant", "scope": "global"}
    ], response)

    persist.assert_awaited_once_with({"tenant": "acme"}, user_id=7)


@pytest.mark.asyncio
async def test_debug_execution_never_persists_global_extractor(monkeypatch):
    persist = AsyncMock(return_value=True)
    monkeypatch.setattr(scenario_runner, "save_variables_to_db", persist)
    engine = ScenarioExecutionEngine(1, user_id=7, _skip_record=True)
    response = {"json": {"token": "debug-only"}, "body": '{"token":"debug-only"}', "headers": {}}
    extracted = await engine._extract_variables([
        {"variableName": "token", "extractorType": "jsonpath", "expression": "$.token", "scope": "global"}
    ], response)
    assert extracted["token"] == "debug-only"
    persist.assert_not_awaited()


@pytest.mark.asyncio
async def test_debug_post_script_never_persists_globals(monkeypatch):
    from fastapi_backend.services.script_engine import ScriptEngine
    persist = AsyncMock(return_value=True)
    monkeypatch.setattr(ScriptEngine, "persist_globals_to_db", persist)
    engine = ScenarioExecutionEngine(1, user_id=7, _skip_record=True)
    engine.context_vars = {}
    engine.session_vars = {}

    async def handler(request):
        return httpx.Response(200, json={"ok": True})

    engine._shared_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    step = {
        **make_step(1, 1), "api_case_name": "debug post script", "api_case_method": "GET",
        "api_case_url": "https://example.test/debug", "api_case_headers": {}, "api_case_params": {},
        "api_case_body": None, "api_case_body_type": "none", "api_case_assert_rules": [],
        "api_case_extractors": [], "post_script": 'pm.globals.set("debug_secret", "temporary");',
    }
    try:
        result = await engine._execute_api_request(step)
    finally:
        await engine._shared_client.aclose()
    assert result["success"] is True
    persist.assert_not_awaited()


@pytest.mark.asyncio
async def test_real_multi_api_chain_extracts_and_reuses_variables(monkeypatch):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            received.append(self.path)
            if self.path == "/seed":
                payload = {"token": "chain-token", "items": [101, 202]}
            else:
                payload = {"accepted": self.path.startswith("/use/chain-token")}
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    db_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        async with factory() as db:
            env = AutoTestEnvironment(
                env_name="chain", base_url=f"http://127.0.0.1:{server.server_port}", variables={}, user_id=1
            )
            seed_case = AutoTestCase(
                name="seed", method="GET", url="/seed", user_id=1,
                assert_rules=[{"field": "status_code", "operator": "equals", "expectedValue": 200}],
                extractors=[
                    {"variableName": "token", "extractorType": "jsonpath", "expression": "$.token"},
                    {"variableName": "items", "extractorType": "jsonpath", "expression": "$.items"},
                ],
            )
            use_case = AutoTestCase(
                name="use", method="GET", url="/use/{{token}}", params={"item": "{{item}}"}, user_id=1,
                assert_rules=[{"field": "status_code", "operator": "equals", "expectedValue": 200}],
            )
            scenario = AutoTestScenario(name="multi-api-chain", user_id=1, fail_fast=True)
            db.add_all([env, seed_case, use_case, scenario])
            await db.flush()
            seed_step = AutoTestScenarioStep(
                scenario_id=scenario.id, api_case_id=seed_case.id, step_order=10, step_type="api_request", is_active=True
            )
            use_step = AutoTestScenarioStep(
                scenario_id=scenario.id, api_case_id=use_case.id, step_order=30, step_type="api_request", is_active=True
            )
            db.add_all([seed_step, use_step])
            await db.flush()
            loop_step = AutoTestScenarioStep(
                scenario_id=scenario.id, step_order=20, step_type="for_each", is_active=True,
                step_config={
                    "reference_mode": "id", "collection": "{{items}}", "item_var": "item",
                    "index_var": "index", "body": [use_step.id],
                },
            )
            db.add(loop_step)
            await db.commit()

        monkeypatch.setattr(scenario_runner, "async_session", factory)
        async def no_globals(_user_id): return {}
        monkeypatch.setattr("fastapi_backend.services.autotest_execution._get_global_variables_cached", no_globals)
        engine = ScenarioExecutionEngine(scenario.id, env.id, user_id=1, _skip_record=True)
        result = await engine.execute()

        assert result["failed_steps"] == 0
        assert engine.context_vars["token"] == "chain-token"
        assert received == ["/seed", "/use/chain-token?item=101", "/use/chain-token?item=202"]
    finally:
        server.shutdown()
        server.server_close()
        await db_engine.dispose()


@pytest.mark.asyncio
async def test_empty_scenario_is_not_reported_as_success(monkeypatch):
    db_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        async with factory() as db:
            scenario = AutoTestScenario(name="empty", user_id=1)
            db.add(scenario)
            await db.commit()
            await db.refresh(scenario)
        monkeypatch.setattr(scenario_runner, "async_session", factory)
        async def no_globals(_user_id): return {}
        monkeypatch.setattr("fastapi_backend.services.autotest_execution._get_global_variables_cached", no_globals)

        result = await ScenarioExecutionEngine(scenario.id, user_id=1, _skip_record=True).execute()

        assert result["status"] == "error"
        assert result["success"] is False
        assert result["total_steps"] == 0
    finally:
        await db_engine.dispose()
