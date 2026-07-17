import json

import httpx
import pytest
from pydantic import ValidationError

from fastapi_backend.services import autotest_request_service as service
from fastapi_backend.schemas.autotest import AutoTestCaseCreate
from fastapi_backend.services.autotest_request_config import mask_request_config, merge_request_config, protect_request_config, reveal_request_config


@pytest.fixture(autouse=True)
def isolate_request_service(monkeypatch):
    async def no_persisted_variables(env_id, variables, user_id=None):
        return dict(variables)

    monkeypatch.setattr(service, "resolve_variables", no_persisted_variables)
    monkeypatch.setattr(service, "validate_url_safety", lambda url: (True, ""))


@pytest.mark.asyncio
async def test_bearer_cookie_and_request_snapshot_are_applied_and_masked(monkeypatch):
    captured = {}

    def handler(request):
        captured["authorization"] = request.headers.get("authorization")
        captured["cookie"] = request.headers.get("cookie")
        return httpx.Response(200, json={"ok": True}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await service.execute_http_request(
            "GET", "https://example.test/items", {}, {}, None,
            request_config={
                "auth": {"type": "bearer", "token": "top-secret"},
                "cookies": {"session": "cookie-secret"},
            }, http_client=client,
        )
    finally:
        await client.aclose()

    assert result["success"] is True
    assert captured == {
        "authorization": "Bearer top-secret",
        "cookie": "session=cookie-secret",
    }
    assert result["request"]["headers"]["authorization"] == "******"
    assert result["request"]["headers"]["cookie"] == "******"


@pytest.mark.asyncio
async def test_api_key_query_and_retry_statuses(monkeypatch):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        status = 503 if calls == 1 else 200
        return httpx.Response(status, json={"call": calls}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await service.execute_http_request(
            "GET", "https://example.test/items", {}, {}, None,
            request_config={
                "auth": {"type": "api_key", "in": "query", "key": "key", "value": "abc"},
                "retry": {"count": 2, "interval_ms": 0, "status_codes": [503]},
            }, http_client=client,
        )
    finally:
        await client.aclose()

    assert result["success"] is True
    assert calls == 2
    assert [item["status_code"] for item in result["attempts"]] == [503, 200]
    assert "key=%2A%2A%2A%2A%2A%2A" in result["request"]["url"]


@pytest.mark.asyncio
async def test_urlencoded_and_graphql_bodies(monkeypatch):
    bodies = []

    def handler(request):
        bodies.append((request.headers.get("content-type"), request.content))
        return httpx.Response(200, json={"ok": True}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        await service.execute_http_request(
            "POST", "https://example.test/form", {}, {}, {"name": "Alice"},
            body_type="x-www-form-urlencoded", http_client=client,
        )
        await service.execute_http_request(
            "POST", "https://example.test/graphql", {}, {}, "query User { user { id } }",
            body_type="graphql", request_config={"graphql_variables": {"id": 7}}, http_client=client,
        )
    finally:
        await client.aclose()

    assert bodies[0][0].startswith("application/x-www-form-urlencoded")
    assert bodies[0][1] == b"name=Alice"
    graphql = json.loads(bodies[1][1])
    assert graphql["query"].startswith("query User")
    assert graphql["variables"] == {"id": 7}


@pytest.mark.asyncio
async def test_empty_json_editor_is_sent_without_a_body_but_invalid_json_still_fails():
    captured = []

    def handler(request):
        captured.append(request.content)
        return httpx.Response(200, json={"ok": True}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        empty = await service.execute_http_request(
            "GET", "https://example.test/items", {}, {}, "   ",
            body_type="json", http_client=client,
        )
        invalid = await service.execute_http_request(
            "POST", "https://example.test/items", {}, {}, "not-json",
            body_type="json", http_client=client,
        )
    finally:
        await client.aclose()

    assert empty["success"] is True
    assert captured == [b""]
    assert invalid["success"] is False
    assert "JSON" in invalid["error"]


@pytest.mark.asyncio
async def test_redirect_target_is_validated_before_following(monkeypatch):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"}, request=request)

    validations = []
    monkeypatch.setattr(
        service,
        "validate_url_safety",
        lambda url: (validations.append(url) or ((False, "private address") if "127.0.0.1" in url else (True, ""))),
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await service.execute_http_request(
            "GET", "https://public.example/start", {}, {}, None,
            request_config={"follow_redirects": True}, http_client=client,
        )
    finally:
        await client.aclose()

    assert result["success"] is False
    assert "重定向目标" in result["error"]
    assert calls == ["https://public.example/start"]
    assert validations[-1] == "http://127.0.0.1/private"


@pytest.mark.asyncio
async def test_cross_origin_redirect_strips_credentials(monkeypatch):
    seen = []

    def handler(request):
        seen.append((request.url.host, request.headers.get("authorization")))
        if request.url.host == "a.test":
            return httpx.Response(302, headers={"location": "https://b.test/final"}, request=request)
        return httpx.Response(200, json={}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await service.execute_http_request(
            "GET", "https://a.test/start", {}, {}, None,
            request_config={"auth": {"type": "bearer", "token": "secret"}, "follow_redirects": True},
            http_client=client,
        )
    finally:
        await client.aclose()
    assert result["success"] is True
    assert seen == [("a.test", "Bearer secret"), ("b.test", None)]


@pytest.mark.asyncio
async def test_redirect_does_not_replay_original_query_params():
    urls = []

    def handler(request):
        urls.append(str(request.url))
        if request.url.host == "a.test":
            return httpx.Response(302, headers={"location": "https://b.test/final"}, request=request)
        return httpx.Response(200, json={}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await service.execute_http_request(
            "GET", "https://a.test/start", {}, {"access_token": "SECRET", "page": "1"}, None,
            request_config={"follow_redirects": True}, http_client=client,
        )
    finally:
        await client.aclose()
    assert result["success"] is True
    assert urls == ["https://a.test/start?access_token=SECRET&page=1", "https://b.test/final"]


@pytest.mark.asyncio
async def test_static_cookies_overlay_session_cookie_without_persisting():
    cookies_seen = []

    def handler(request):
        cookies_seen.append(request.headers.get("cookie"))
        return httpx.Response(200, json={}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client.cookies.set("login", "session", domain="example.test", path="/")
    try:
        await service.execute_http_request(
            "GET", "https://example.test/a", {}, {}, None,
            request_config={"cookies": {"tenant": "x"}}, http_client=client,
        )
        await service.execute_http_request("GET", "https://example.test/b", {}, {}, None, http_client=client)
    finally:
        await client.aclose()
    assert cookies_seen == ["login=session; tenant=x", "login=session"]


@pytest.mark.asyncio
async def test_decoding_error_recovers_with_identity_encoding(monkeypatch):
    calls = []

    class DecodeThenSuccess:
        cookies = httpx.Cookies()

        async def request(self, method, url, **kwargs):
            calls.append(dict(kwargs.get("headers") or {}))
            if len(calls) == 1:
                raise httpx.DecodingError("bad gzip")
            request = httpx.Request(method, url, headers=kwargs.get("headers"))
            return httpx.Response(200, json={"ok": True}, request=request)

    result = await service.execute_http_request(
        "GET", "https://example.test/data", {}, {}, None,
        http_client=DecodeThenSuccess(), resolve_persisted_variables=False,
    )
    assert result["success"] is True
    assert calls[1]["Accept-Encoding"] == "identity"


def test_response_body_expression_assertion_and_quoted_jsonpath_key():
    from fastapi_backend.services.autotest_assertion_engine import execute_assertions
    from fastapi_backend.utils.autotest_helpers import extract_jsonpath_value

    body = {"user": {"id": 7}, "user-name": "alice"}
    result = execute_assertions(
        [{"target": "response_body", "expression": "$.user.id", "operator": "==", "expected": 7}],
        200, body,
    )
    assert result["passed"] is True
    assert extract_jsonpath_value(body, '$["user-name"]') == "alice"


@pytest.mark.asyncio
async def test_default_clients_do_not_share_target_cookies(monkeypatch):
    seen_cookies = []

    def handler(request):
        seen_cookies.append(request.headers.get("cookie"))
        return httpx.Response(200, headers={"set-cookie": "session=tenant-a"}, json={}, request=request)

    real_client = httpx.AsyncClient

    def isolated_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(service.httpx, "AsyncClient", isolated_client)
    await service.execute_http_request("GET", "https://example.test/a", {}, {}, None)
    await service.execute_http_request("GET", "https://example.test/b", {}, {}, None)
    assert seen_cookies == [None, None]


@pytest.mark.asyncio
async def test_dynamic_auth_variables_and_non_idempotent_retry_policy(monkeypatch):
    requests_seen = []

    def handler(request):
        requests_seen.append(request)
        return httpx.Response(503, json={}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await service.execute_http_request(
            "POST", "https://example.test/order", {}, {}, {"count": 0}, variables={"token": 'runtime"token\\line'},
            request_config={
                "auth": {"type": "bearer", "token": "{{token}}"},
                "retry": {"count": 3, "status_codes": [503]},
            }, http_client=client,
        )
    finally:
        await client.aclose()

    assert len(requests_seen) == 1
    assert requests_seen[0].headers["authorization"] == 'Bearer runtime"token\\line'
    assert json.loads(requests_seen[0].content) == {"count": 0}
    assert len(result["attempts"]) == 1


@pytest.mark.asyncio
async def test_multipart_file_upload_uses_real_file_part(monkeypatch):
    captured = {}

    def handler(request):
        captured["content_type"] = request.headers["content-type"]
        captured["body"] = request.content
        return httpx.Response(200, json={}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await service.execute_http_request(
            "POST", "https://example.test/upload", {}, {},
            {
                "description": "evidence",
                "attachment": {
                    "type": "file", "filename": "proof.txt", "content_type": "text/plain",
                    "content_base64": "aGVsbG8=",
                },
            }, body_type="form-data", http_client=client,
        )
    finally:
        await client.aclose()

    assert result["success"] is True
    assert captured["content_type"].startswith("multipart/form-data; boundary=")
    assert b'name="description"' in captured["body"]
    assert b'filename="proof.txt"' in captured["body"]
    assert b"hello" in captured["body"]


def test_request_config_schema_rejects_invalid_values():
    with pytest.raises(ValidationError):
        AutoTestCaseCreate(
            name="bad", url="https://example.test", request_config={
                "auth": {"type": "bearer", "token": ""},
                "timeout_ms": -1,
                "retry": {"count": 99, "status_codes": [999]},
            },
        )


def test_request_secrets_are_encrypted_at_rest_and_masked_for_lists():
    source = {
        "auth": {"type": "basic", "username": "alice", "password": "secret"},
        "cookies": {"session": "cookie-secret"},
    }
    protected = protect_request_config(source)
    assert "secret" not in json.dumps(protected)
    assert reveal_request_config(protected) == source
    masked = mask_request_config(protected)
    assert masked["auth"]["password"] == "******"
    assert masked["cookies"]["session"] == "******"
    merged = merge_request_config(protected, {"timeout_ms": 5000, "auth": {"password": "******"}})
    revealed = reveal_request_config(merged)
    assert revealed["auth"]["password"] == "secret"
    assert revealed["timeout_ms"] == 5000


def test_sync_task_reload_marks_interrupted_work_failed(tmp_path, monkeypatch):
    from fastapi_backend.services import autotest_task_store as store
    task_file = tmp_path / "batch.json"
    task_file.write_text(json.dumps({"task_id": "batch", "status": "PROGRESS"}), encoding="utf-8")
    monkeypatch.setattr(store, "_get_tasks_dir", lambda: tmp_path)
    store._task_store.clear()
    store._load_all_tasks_sync()
    assert store._task_store["batch"]["status"] == "failed"
    assert "重启" in store._task_store["batch"]["error"]


@pytest.mark.asyncio
async def test_body_limit_counts_streamed_chunks_without_content_length():
    from fastapi_backend.middleware.request_body_limit import RequestBodyLimitMiddleware
    reached_app = False

    async def app(scope, receive, send):
        nonlocal reached_app
        reached_app = True
        while (await receive()).get("more_body"):
            pass

    messages = iter([
        {"type": "http.request", "body": b"1234", "more_body": True},
        {"type": "http.request", "body": b"5678", "more_body": False},
    ])
    sent = []
    async def receive(): return next(messages)
    async def send(message): sent.append(message)
    middleware = RequestBodyLimitMiddleware(app, max_bytes=5)
    await middleware({"type": "http", "path": "/api/auto-test/send"}, receive, send)
    assert reached_app is True
    assert sent[0]["status"] == 413
