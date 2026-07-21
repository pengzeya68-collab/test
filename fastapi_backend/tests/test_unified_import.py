import io
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from fastapi_backend.models.autotest import AutoTestCase, ImportJob
from fastapi_backend.services.unified_import import parse_import
from fastapi_backend.tests.test_autotest_compat import (
    autotest_client,
    autotest_engine,
    autotest_session_factory,
)


def _postman_collection(name: str, request_name: str = "创建订单") -> bytes:
    return json.dumps(
        {
            "info": {
                "name": name,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [
                {
                    "name": request_name,
                    "request": {
                        "method": "POST",
                        "url": {"raw": "https://api.example.test/orders?token=real-token"},
                        "header": [
                            {"key": "Authorization", "value": "Bearer real-secret"},
                            {"key": "Cookie", "value": "session=real-cookie"},
                            {"key": "Content-Type", "value": "application/json"},
                        ],
                        "body": {"mode": "raw", "raw": '{"sku":"A-1","password":"unsafe"}'},
                    },
                }
            ],
        }
    ).encode("utf-8")


def test_unified_import_parses_openapi_swagger_curl_and_apipost():
    openapi = b"""
openapi: 3.0.3
info: {title: Store API, version: '1'}
servers: [{url: https://shop.example.test}]
paths:
  /orders/{orderId}:
    get:
      summary: Read order
      parameters:
        - {name: orderId, in: path, required: true, schema: {type: string}}
        - {name: verbose, in: query, schema: {type: boolean}}
      responses: {'200': {description: ok}}
"""
    source_type, candidates = parse_import(openapi, filename="openapi.yaml")
    assert source_type == "openapi"
    assert candidates[0]["url"] == "https://shop.example.test/orders/{{orderId}}?verbose=False"
    assert candidates[0]["assert_rules"][0]["expected"] == 200

    swagger = json.dumps(
        {
            "swagger": "2.0",
            "info": {"title": "Legacy", "version": "1"},
            "host": "legacy.example.test",
            "paths": {"/health": {"get": {"responses": {"204": {"description": "ok"}}}}},
        }
    ).encode("utf-8")
    assert parse_import(swagger)[0] == "swagger"

    curl = b"curl -X POST 'https://api.example.test/orders' -H 'Authorization: Bearer real-token' -d '{\"password\":\"real\"}'"
    source_type, candidates = parse_import(curl)
    assert source_type == "curl"
    assert candidates[0]["headers"]["Authorization"] == "{{AUTHORIZATION}}"
    assert candidates[0]["payload"]["password"] == "{{PASSWORD}}"

    apipost = json.dumps(
        {
            "apiCollection": [
                {"name": "Get profile", "request": {"method": "GET", "url": "https://api.example.test/profile"}}
            ],
        }
    ).encode("utf-8")
    source_type, candidates = parse_import(apipost)
    assert source_type == "apipost"
    assert candidates[0]["name"] == "Get profile"


@pytest.mark.asyncio
async def test_preview_and_explicit_update_are_audited(autotest_client, autotest_session_factory):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    app.dependency_overrides[get_current_user] = _admin_user
    initial = _postman_collection("Store", "原始订单请求")
    preview = autotest_client.post(
        "/api/auto-test/import/preview",
        files={"file": ("store.postman_collection.json", io.BytesIO(initial), "application/json")},
        data={"source_type": "auto"},
    )
    assert preview.status_code == 200
    candidate = preview.json()["candidates"][0]
    assert candidate["source_type"] == "postman"
    assert candidate["headers"]["Authorization"] == "{{AUTHORIZATION}}"
    assert "Cookie" not in candidate["headers"]
    assert candidate["payload"]["password"] == "{{PASSWORD}}"
    assert candidate["conflict_count"] == 0

    created = autotest_client.post(
        "/api/auto-test/import/commit",
        files={"file": ("store.json", io.BytesIO(initial), "application/json")},
        data={"source_type": "postman", "conflict_strategy": "skip"},
    )
    assert created.status_code == 200
    assert created.json()["imported_count"] == 1

    updated_source = _postman_collection("Store", "更新后的订单请求")
    updated = autotest_client.post(
        "/api/auto-test/import/commit",
        files={"file": ("store.json", io.BytesIO(updated_source), "application/json")},
        data={"source_type": "postman", "conflict_strategy": "update"},
    )
    assert updated.status_code == 200
    assert updated.json()["updated_count"] == 1
    assert updated.json()["imported_count"] == 0

    async with autotest_session_factory() as db:
        cases = list((await db.scalars(select(AutoTestCase))).all())
        jobs = list((await db.scalars(select(ImportJob).order_by(ImportJob.created_at))).all())
    assert len(cases) == 1
    assert cases[0].name == "更新后的订单请求"
    assert [job.status for job in jobs] == ["previewed", "completed", "completed"]
    assert all((job.summary or {}).get("sensitive_values_redacted") for job in jobs)


@pytest.mark.asyncio
async def test_invalid_source_creates_a_redacted_failure_audit_job(autotest_client, autotest_session_factory):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    app.dependency_overrides[get_current_user] = _admin_user
    response = autotest_client.post(
        "/api/auto-test/import/preview",
        files={"file": ("invalid.txt", io.BytesIO(b"not a valid import source"), "text/plain")},
        data={"source_type": "auto"},
    )
    assert response.status_code == 422
    async with autotest_session_factory() as db:
        job = await db.scalar(select(ImportJob).where(ImportJob.status == "failed"))
    assert job is not None
    assert job.summary["sensitive_values_redacted"] is True
    assert "not a valid import source" not in (job.error_summary or "")


@pytest.mark.asyncio
async def test_capture_conversion_requires_confirmation_and_preserves_authored_scripts(
    autotest_client, autotest_session_factory
):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    app.dependency_overrides[get_current_user] = _admin_user
    created = autotest_client.post("/api/auto-test/import/captures", json={"origin": "desktop_browser"})
    assert created.status_code == 201
    session_id = created.json()["id"]
    appended = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges",
        json={
            "exchanges": [
                {
                    "resourceType": "fetch",
                    "method": "POST",
                    "url": "https://shop.example.test/orders",
                    "requestHeaders": {"Content-Type": "application/json"},
                    "requestBody": {"sku": "A-1"},
                    "status": 201,
                    "responseBody": {"id": "order-1"},
                }
            ]
        },
    )
    assert appended.status_code == 200
    exchange_id = appended.json()["exchange_ids"][0]
    assert autotest_client.post(f"/api/auto-test/import/captures/{session_id}/complete").status_code == 200

    first = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/convert",
        json={
            "exchange_ids": [exchange_id],
            "conflict_strategy": "skip",
        },
    )
    assert first.status_code == 200
    case_id = first.json()["case_ids"][0]
    async with autotest_session_factory() as db:
        case = await db.get(AutoTestCase, case_id)
        case.pre_script = "keep this authored setup"
        await db.commit()

    rejected = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/convert",
        json={
            "exchange_ids": [exchange_id],
            "conflict_strategy": "update",
        },
    )
    assert rejected.status_code == 422

    dependency_review = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/convert",
        json={
            "exchange_ids": [exchange_id],
            "conflict_strategy": "skip",
            "create_scenario": True,
        },
    )
    assert dependency_review.status_code == 422
    invalid_mapping = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/convert",
        json={
            "exchange_ids": [exchange_id],
            "conflict_strategy": "skip",
            "variable_mappings": [
                {
                    "source_exchange_id": exchange_id,
                    "variable_name": "order_id",
                    "json_path": "$.id",
                    "targets": [{"exchange_id": exchange_id, "location": "params.id"}],
                }
            ],
        },
    )
    assert invalid_mapping.status_code == 422

    updated = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/convert",
        json={
            "exchange_ids": [exchange_id],
            "conflict_strategy": "update",
            "confirm_update": True,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["updated_count"] == 1
    assert updated.json()["imported_count"] == 0
    async with autotest_session_factory() as db:
        case = await db.get(AutoTestCase, case_id)
        assert case.pre_script == "keep this authored setup"


@pytest.mark.asyncio
async def test_incomplete_capture_can_be_explicitly_cancelled(autotest_client):
    from fastapi_backend.deps.auth import get_current_user
    from fastapi_backend.main import app

    async def _admin_user():
        return SimpleNamespace(id=1, username="admin", is_admin=True, is_super_admin=True, role_id=None)

    app.dependency_overrides[get_current_user] = _admin_user
    created = autotest_client.post("/api/auto-test/import/captures", json={"origin": "desktop_browser"})
    assert created.status_code == 201
    cancelled = autotest_client.post(
        f"/api/auto-test/import/captures/{created.json()['id']}/cancel",
        json={"reason": "network sync was explicitly discarded"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert autotest_client.post(f"/api/auto-test/import/captures/{created.json()['id']}/complete").status_code == 409
