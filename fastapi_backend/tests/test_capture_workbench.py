"""Regression coverage for the capture workbench's safety and evidence rules."""

import io
import json
from datetime import datetime, timedelta, timezone

import pytest

from fastapi_backend.core import rbac
from fastapi_backend.models.autotest import CaptureSession
from fastapi_backend.services import autotest_request_service
from fastapi_backend.tests.test_autotest_compat import autotest_client, autotest_engine, autotest_session_factory


@pytest.fixture(autouse=True)
def _allow_capture_permissions(monkeypatch):
    async def all_permissions(*_args, **_kwargs):
        return {"*"}

    monkeypatch.setattr(rbac, "get_user_permissions", all_permissions)


def _create_capture(client):
    response = client.post("/api/auto-test/import/captures", json={"origin": "desktop_browser"})
    assert response.status_code == 201
    return response.json()["id"]


def test_capture_preserves_repeated_business_calls_but_retries_are_idempotent(autotest_client):
    session_id = _create_capture(autotest_client)
    exchange = {
        "captureEventId": "first-event",
        "resourceType": "fetch",
        "method": "POST",
        "url": "https://shop.example.test/orders",
        "requestHeaders": {"content-type": "application/json"},
        "requestBody": {"sku": "A-1", "token": "do-not-store"},
        "status": 201,
        "responseBody": {"id": "order-1"},
    }
    second = {**exchange, "captureEventId": "second-event", "responseBody": {"id": "order-2"}}
    append = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges", json={"exchanges": [exchange, second]}
    )
    assert append.status_code == 200
    assert append.json()["accepted"] == 2
    retry = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges", json={"exchanges": [exchange, second]}
    )
    assert retry.status_code == 200
    assert retry.json()["accepted"] == 0
    detail = autotest_client.get(f"/api/auto-test/import/captures/{session_id}")
    assert detail.json()["total"] == 2
    assert "do-not-store" not in str(detail.json())


def test_capture_keeps_page_failures_for_diagnosis_but_refuses_case_conversion(autotest_client):
    session_id = _create_capture(autotest_client)
    append = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges",
        json={
            "exchanges": [
                {
                    "captureEventId": "failed-page",
                    "resourceType": "document",
                    "method": "GET",
                    "url": "https://shop.example.test/checkout",
                    "status": 0,
                    "failureReason": "net::ERR_CONNECTION_RESET token=never-leak",
                }
            ]
        },
    )
    assert append.status_code == 200
    exchange_id = append.json()["exchange_ids"][0]
    inspected = autotest_client.get(f"/api/auto-test/import/captures/{session_id}/exchanges/{exchange_id}")
    assert inspected.status_code == 200
    assert inspected.json()["convertible"] is False
    assert "never-leak" not in str(inspected.json())
    assert autotest_client.post(f"/api/auto-test/import/captures/{session_id}/complete").status_code == 200
    converted = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/convert", json={"exchange_ids": [exchange_id]}
    )
    assert converted.status_code == 422


def test_abandoned_capture_is_closed_when_the_workbench_is_opened(autotest_client, autotest_session_factory):
    session_id = _create_capture(autotest_client)

    async def age_capture():
        async with autotest_session_factory() as db:
            capture = await db.get(CaptureSession, session_id)
            capture.started_at = datetime.now(timezone.utc) - timedelta(hours=25)
            await db.commit()

    import asyncio

    asyncio.run(age_capture())
    captures = autotest_client.get("/api/auto-test/import/captures")
    assert captures.status_code == 200
    item = next(row for row in captures.json()["captures"] if row["id"] == session_id)
    assert item["status"] == "cancelled"
    assert "expired" in item["failure_reason"]


def test_har_enters_review_workbench_before_any_case_is_created(autotest_client):
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "POST",
                        "url": "https://shop.example.test/orders?token=do-not-store",
                        "headers": [{"name": "Content-Type", "value": "application/json"}],
                        "postData": {"mimeType": "application/json", "text": '{"password":"do-not-store"}'},
                    },
                    "response": {"status": 201, "content": {"mimeType": "application/json", "text": '{"id":"o-1"}'}},
                    "time": 29,
                }
            ]
        }
    }
    imported = autotest_client.post(
        "/api/auto-test/import/captures/har",
        files={"file": ("checkout.har", io.BytesIO(json.dumps(har).encode()), "application/json")},
    )
    assert imported.status_code == 201
    detail = autotest_client.get(f"/api/auto-test/import/captures/{imported.json()['id']}")
    assert detail.status_code == 200
    assert detail.json()["origin"] == "har_import"
    assert detail.json()["total"] == 1
    assert "do-not-store" not in str(detail.json())


def test_replay_needs_confirmation_and_returns_a_redacted_semantic_diff(monkeypatch, autotest_client):
    session_id = _create_capture(autotest_client)
    append = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges",
        json={
            "exchanges": [
                {
                    "captureEventId": "replayable",
                    "resourceType": "xhr",
                    "method": "GET",
                    "url": "https://shop.example.test/orders/1",
                    "status": 200,
                    "responseBody": {"status": "ok", "token": "baseline-secret", "total": 1},
                }
            ]
        },
    )
    assert append.status_code == 200
    exchange_id = append.json()["exchange_ids"][0]
    rejected = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges/{exchange_id}/replay", json={}
    )
    assert rejected.status_code == 422

    async def fake_execute(**_kwargs):
        return {
            "success": True,
            "status_code": 200,
            "elapsed_ms": 41,
            "headers": {"content-type": "application/json", "set-cookie": "private"},
            "response_content": {"status": "changed", "token": "replay-secret", "total": 1},
            "attempts": [{"attempt": 1, "status_code": 200, "elapsed_ms": 41}],
        }

    monkeypatch.setattr(autotest_request_service, "execute_http_request", fake_execute)
    replayed = autotest_client.post(
        f"/api/auto-test/import/captures/{session_id}/exchanges/{exchange_id}/replay",
        json={"confirm_replay": True, "variables": {"ORDER_ID": "1"}},
    )
    assert replayed.status_code == 200
    result = replayed.json()
    assert result["comparison"]["status_matches"] is True
    assert any(item["path"] == "$.status" for item in result["comparison"]["body_differences"])
    assert "baseline-secret" not in str(result)
    assert "replay-secret" not in str(result)
    assert "private" not in str(result)
