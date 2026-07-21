"""End-to-end coverage for signed, replay-safe external suite triggers."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationWebhookReceipt,
    AutoTestScenario,
    TestSuite as SuiteModel,
    TestSuiteScenario as SuiteScenarioModel,
)
from fastapi import HTTPException
from fastapi_backend.services.webhook_execution import _validate_timestamp, sign_webhook_payload
from fastapi_backend.tests.test_autotest_compat import (
    autotest_client,
    autotest_engine,
    autotest_session_factory,
)


async def _admin_user(user_id: int = 1):
    return SimpleNamespace(
        id=user_id,
        username=f"webhook-owner-{user_id}",
        is_admin=True,
        is_super_admin=True,
        is_active=True,
        role_id=None,
    )


async def _create_suite(session_factory, user_id: int = 1) -> SuiteModel:
    async with session_factory() as db:
        scenario = AutoTestScenario(name=f"Webhook scenario {user_id}", user_id=user_id, is_active=True)
        suite = SuiteModel(name=f"Webhook suite {user_id}", user_id=user_id, kind="scenario", is_active=True)
        db.add_all([scenario, suite])
        await db.flush()
        db.add(SuiteScenarioModel(suite_id=suite.id, scenario_id=scenario.id, sort_order=10))
        await db.commit()
        await db.refresh(suite)
        return suite


def _headers(secret: str, body: bytes, event_id: str = "ci-build-101", timestamp: int | None = None) -> dict[str, str]:
    raw_timestamp = str(timestamp if timestamp is not None else int(time.time()))
    return {
        "X-TestMaster-Timestamp": raw_timestamp,
        "X-TestMaster-Signature": "sha256=" + sign_webhook_payload(secret, raw_timestamp, body),
        "X-TestMaster-Event-Id": event_id,
    }


@pytest.mark.asyncio
async def test_signed_webhook_is_replay_safe_and_exposes_only_its_own_execution(
    autotest_client, autotest_session_factory, monkeypatch
):
    suite = await _create_suite(autotest_session_factory)
    dispatched: list[int] = []

    async def _dispatch(execution_id: int):
        dispatched.append(execution_id)

    monkeypatch.setattr("fastapi_backend.routers.autotest_webhooks.dispatch_suite_execution", _dispatch)
    app.dependency_overrides[get_current_user] = _admin_user

    created = autotest_client.post("/api/auto-test/webhooks", json={"suite_id": suite.id, "name": "CI regression"})
    assert created.status_code == 201, created.text
    webhook = created.json()
    assert webhook["signing_secret"]
    assert webhook["inbound_url"].endswith(webhook["id"])
    assert webhook["signature_headers"]["algorithm"] == "HMAC-SHA256(timestamp + '.' + raw_body)"

    listed = autotest_client.get("/api/auto-test/webhooks")
    assert listed.status_code == 200, listed.text
    assert "signing_secret" not in listed.json()["items"][0]

    second_created = autotest_client.post("/api/auto-test/webhooks", json={"suite_id": suite.id, "name": "Other CI"})
    assert second_created.status_code == 201, second_created.text
    other_webhook = second_created.json()

    payload = b'{"build":"101","branch":"main"}'
    inbound = f"/api/auto-test/webhooks/inbound/{webhook['id']}"
    accepted = autotest_client.post(inbound, content=payload, headers=_headers(webhook["signing_secret"], payload))
    assert accepted.status_code == 202, accepted.text
    result = accepted.json()
    assert result["duplicate"] is False
    assert result["status"] == "queued"
    assert len(dispatched) == 1

    replayed = autotest_client.post(inbound, content=payload, headers=_headers(webhook["signing_secret"], payload))
    assert replayed.status_code == 202, replayed.text
    assert replayed.json()["duplicate"] is True
    assert replayed.json()["execution_id"] == result["execution_id"]
    # Re-dispatching a still queued execution closes the broker-delivery gap;
    # the runner itself claims the record atomically.
    assert len(dispatched) == 2

    conflict = autotest_client.post(
        inbound,
        content=b'{"build":"different"}',
        headers=_headers(webhook["signing_secret"], b'{"build":"different"}'),
    )
    assert conflict.status_code == 409, conflict.text

    expired = autotest_client.post(
        inbound,
        content=b"{}",
        headers=_headers(
            webhook["signing_secret"], b"{}", event_id="ci-build-expired", timestamp=int(time.time()) - 1000
        ),
    )
    assert expired.status_code == 401, expired.text

    invalid_signature = autotest_client.post(
        inbound,
        content=b"{}",
        headers={
            "X-TestMaster-Timestamp": str(int(time.time())),
            "X-TestMaster-Signature": "sha256=" + "0" * 64,
            "X-TestMaster-Event-Id": "ci-build-invalid-signature",
        },
    )
    assert invalid_signature.status_code == 401, invalid_signature.text
    assert invalid_signature.json()["code"] == "HTTP_401"

    # HTTP clients reject non-ASCII headers before the server. Cover the
    # service boundary directly so a proxy that permits them still gets 401.
    with pytest.raises(HTTPException) as non_ascii_timestamp:
        _validate_timestamp("\u0661\u0662\u0663", 300)
    assert non_ascii_timestamp.value.status_code == 401

    status_endpoint = f"/api/auto-test/webhooks/inbound/{webhook['id']}/executions/{result['execution_id']}"
    status_response = autotest_client.get(status_endpoint, headers=_headers(webhook["signing_secret"], b""))
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["execution_id"] == result["execution_id"]

    foreign_status = autotest_client.get(
        f"/api/auto-test/webhooks/inbound/{other_webhook['id']}/executions/{result['execution_id']}",
        headers=_headers(other_webhook["signing_secret"], b""),
    )
    assert foreign_status.status_code == 404, foreign_status.text

    async with autotest_session_factory() as db:
        executions = list((await db.scalars(select(AutomationExecution))).all())
        receipts = list((await db.scalars(select(AutomationWebhookReceipt))).all())
        assert len(executions) == 1
        assert len(receipts) == 1
        assert receipts[0].event_id == "ci-build-101"


@pytest.mark.asyncio
async def test_webhook_management_validates_owner_and_stops_inbound_events(
    autotest_client, autotest_session_factory, monkeypatch
):
    owner_suite = await _create_suite(autotest_session_factory, user_id=1)
    foreign_suite = await _create_suite(autotest_session_factory, user_id=2)

    async def _no_op_dispatch(_execution_id: int):
        return None

    monkeypatch.setattr("fastapi_backend.routers.autotest_webhooks.dispatch_suite_execution", _no_op_dispatch)
    app.dependency_overrides[get_current_user] = _admin_user
    created = autotest_client.post("/api/auto-test/webhooks", json={"suite_id": owner_suite.id, "name": "Owner only"})
    assert created.status_code == 201, created.text
    webhook = created.json()

    async def _foreign_user():
        return await _admin_user(2)

    app.dependency_overrides[get_current_user] = _foreign_user
    assert autotest_client.get("/api/auto-test/webhooks").json()["total"] == 0
    cannot_manage = autotest_client.patch(f"/api/auto-test/webhooks/{webhook['id']}", json={"is_active": False})
    assert cannot_manage.status_code == 404, cannot_manage.text
    cannot_create = autotest_client.post(
        "/api/auto-test/webhooks", json={"suite_id": owner_suite.id, "name": "not mine"}
    )
    assert cannot_create.status_code == 404, cannot_create.text
    own_created = autotest_client.post("/api/auto-test/webhooks", json={"suite_id": foreign_suite.id, "name": "owned"})
    assert own_created.status_code == 201, own_created.text

    app.dependency_overrides[get_current_user] = _admin_user
    bad_boolean = autotest_client.patch(f"/api/auto-test/webhooks/{webhook['id']}", json={"is_active": "false"})
    assert bad_boolean.status_code == 422, bad_boolean.text
    disabled = autotest_client.patch(f"/api/auto-test/webhooks/{webhook['id']}", json={"is_active": False})
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["is_active"] is False

    inbound = autotest_client.post(
        f"/api/auto-test/webhooks/inbound/{webhook['id']}",
        content=b"{}",
        headers=_headers(webhook["signing_secret"], b"{}", event_id="after-disable"),
    )
    assert inbound.status_code == 404, inbound.text


@pytest.mark.asyncio
async def test_rotated_webhook_secret_rejects_the_previous_signature(
    autotest_client, autotest_session_factory, monkeypatch
):
    suite = await _create_suite(autotest_session_factory)

    async def _no_op_dispatch(_execution_id: int):
        return None

    monkeypatch.setattr("fastapi_backend.routers.autotest_webhooks.dispatch_suite_execution", _no_op_dispatch)
    app.dependency_overrides[get_current_user] = _admin_user
    created = autotest_client.post("/api/auto-test/webhooks", json={"suite_id": suite.id, "name": "Rotate me"})
    assert created.status_code == 201, created.text
    webhook = created.json()
    rotated = autotest_client.post(f"/api/auto-test/webhooks/{webhook['id']}/rotate-secret")
    assert rotated.status_code == 200, rotated.text
    new_secret = rotated.json()["signing_secret"]
    payload = b'{"build":"rotated"}'
    inbound = f"/api/auto-test/webhooks/inbound/{webhook['id']}"
    old_secret_attempt = autotest_client.post(
        inbound,
        content=payload,
        headers=_headers(webhook["signing_secret"], payload, event_id="old-secret"),
    )
    assert old_secret_attempt.status_code == 401, old_secret_attempt.text
    new_secret_attempt = autotest_client.post(
        inbound,
        content=payload,
        headers=_headers(new_secret, payload, event_id="new-secret"),
    )
    assert new_secret_attempt.status_code == 202, new_secret_attempt.text
