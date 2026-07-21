"""Management and public ingress endpoints for signed suite webhooks."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationWebhook,
    AutomationWebhookReceipt,
    TestSuite,
)
from fastapi_backend.models.models import User
from fastapi_backend.services.suite_execution_service import dispatch_suite_execution
from fastapi_backend.services.webhook_execution import (
    authenticate_webhook_request,
    create_webhook_execution,
    encrypt_webhook_secret,
    generate_webhook_secret,
    normalize_clock_skew,
)

router = APIRouter(prefix="/api/auto-test/webhooks", tags=["Regression Webhooks"])
_MAX_WEBHOOK_BODY_BYTES = 1024 * 1024


def _inbound_url(webhook_id: str) -> str:
    return f"/api/auto-test/webhooks/inbound/{webhook_id}"


def _webhook_payload(webhook: AutomationWebhook, include_secret: str | None = None) -> dict[str, Any]:
    payload = {
        "id": webhook.id,
        "name": webhook.name,
        "suite_id": webhook.suite_id,
        "is_active": webhook.is_active,
        "allowed_clock_skew_seconds": webhook.allowed_clock_skew_seconds,
        "inbound_url": _inbound_url(webhook.id),
        "status_url_template": f"{_inbound_url(webhook.id)}/executions/{{execution_id}}",
        "signature_headers": {
            "timestamp": "X-TestMaster-Timestamp",
            "signature": "X-TestMaster-Signature",
            "event_id": "X-TestMaster-Event-Id",
            "algorithm": "HMAC-SHA256(timestamp + '.' + raw_body)",
        },
        "created_at": webhook.created_at,
        "updated_at": webhook.updated_at,
    }
    if include_secret is not None:
        payload["signing_secret"] = include_secret
        payload["secret_notice"] = "签名密钥只会在本次响应显示，请立即保存。"
    return payload


async def _owned_suite(db: AsyncSession, suite_id: Any, user_id: int) -> TestSuite:
    try:
        normalized_id = int(suite_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="suite_id 必须是整数") from exc
    suite = await db.scalar(select(TestSuite).where(TestSuite.id == normalized_id, TestSuite.user_id == user_id))
    if suite is None:
        raise HTTPException(status_code=404, detail="测试套件不存在或无权访问")
    return suite


async def _owned_webhook(db: AsyncSession, webhook_id: str, user_id: int) -> AutomationWebhook:
    webhook = await db.scalar(
        select(AutomationWebhook).where(AutomationWebhook.id == webhook_id, AutomationWebhook.user_id == user_id)
    )
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook 不存在或无权访问")
    return webhook


async def _read_raw_body(request: Request) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > _MAX_WEBHOOK_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Webhook 请求体不能超过 1 MB")
    body = await request.body()
    if len(body) > _MAX_WEBHOOK_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Webhook 请求体不能超过 1 MB")
    return body


@router.post("", status_code=status.HTTP_201_CREATED)
@audit_log("create", "webhook")
async def create_webhook(
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("webhook:manage")),
    db: AsyncSession = Depends(get_autotest_db),
):
    suite = await _owned_suite(db, body.get("suite_id"), current_user.id)
    name = str(body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Webhook 名称不能为空")
    secret = generate_webhook_secret()
    webhook = AutomationWebhook(
        user_id=current_user.id,
        suite_id=suite.id,
        name=name[:200],
        signing_secret_encrypted=encrypt_webhook_secret(secret),
        is_active=True,
        allowed_clock_skew_seconds=normalize_clock_skew(body.get("allowed_clock_skew_seconds", 300)),
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return _webhook_payload(webhook, include_secret=secret)


@router.get("")
async def list_webhooks(
    suite_id: int | None = None,
    current_user: User = Depends(require_permissions("webhook:manage")),
    db: AsyncSession = Depends(get_autotest_db),
):
    query = select(AutomationWebhook).where(AutomationWebhook.user_id == current_user.id)
    if suite_id is not None:
        query = query.where(AutomationWebhook.suite_id == suite_id)
    rows = list((await db.scalars(query.order_by(AutomationWebhook.created_at.desc()))).all())
    return {"items": [_webhook_payload(webhook) for webhook in rows], "total": len(rows)}


@router.patch("/{webhook_id}")
@audit_log("update", "webhook", resource_id_param="webhook_id")
async def update_webhook(
    webhook_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("webhook:manage")),
    db: AsyncSession = Depends(get_autotest_db),
):
    webhook = await _owned_webhook(db, webhook_id, current_user.id)
    if "name" in body:
        name = str(body.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Webhook 名称不能为空")
        webhook.name = name[:200]
    if "is_active" in body:
        if not isinstance(body["is_active"], bool):
            raise HTTPException(status_code=422, detail="is_active 必须是布尔值")
        webhook.is_active = body["is_active"]
    if "allowed_clock_skew_seconds" in body:
        webhook.allowed_clock_skew_seconds = normalize_clock_skew(body["allowed_clock_skew_seconds"])
    await db.commit()
    await db.refresh(webhook)
    return _webhook_payload(webhook)


@router.post("/{webhook_id}/rotate-secret")
@audit_log("rotate_secret", "webhook", resource_id_param="webhook_id")
async def rotate_webhook_secret(
    webhook_id: str,
    current_user: User = Depends(require_permissions("webhook:manage")),
    db: AsyncSession = Depends(get_autotest_db),
):
    webhook = await _owned_webhook(db, webhook_id, current_user.id)
    secret = generate_webhook_secret()
    webhook.signing_secret_encrypted = encrypt_webhook_secret(secret)
    await db.commit()
    await db.refresh(webhook)
    return _webhook_payload(webhook, include_secret=secret)


@router.post("/inbound/{webhook_id}", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(
    webhook_id: str,
    request: Request,
    db: AsyncSession = Depends(get_autotest_db),
):
    raw_body = await _read_raw_body(request)
    webhook = await authenticate_webhook_request(
        db,
        webhook_id,
        request.headers.get("X-TestMaster-Timestamp"),
        request.headers.get("X-TestMaster-Signature"),
        raw_body,
    )
    execution, duplicate = await create_webhook_execution(
        db,
        webhook,
        request.headers.get("X-TestMaster-Event-Id"),
        raw_body,
    )
    if execution.status == "queued":
        try:
            await dispatch_suite_execution(execution.id)
        except Exception:
            # The execution row is durable. A retry with the same event ID will
            # re-dispatch it safely because the runner claims queued work atomically.
            raise HTTPException(status_code=503, detail="执行任务暂时无法调度，请使用相同事件 ID 重试")
    return {
        "accepted": True,
        "duplicate": duplicate,
        "execution_id": execution.public_id,
        "status": execution.status,
        "status_url": f"{_inbound_url(webhook.id)}/executions/{execution.public_id}",
    }


@router.get("/inbound/{webhook_id}/executions/{execution_id}")
async def get_webhook_execution_status(
    webhook_id: str,
    execution_id: str,
    request: Request,
    db: AsyncSession = Depends(get_autotest_db),
):
    # GET is independently signed over an empty request body. It deliberately
    # carries no event ID because status queries are read-only and non-replaying.
    webhook = await authenticate_webhook_request(
        db,
        webhook_id,
        request.headers.get("X-TestMaster-Timestamp"),
        request.headers.get("X-TestMaster-Signature"),
        b"",
    )
    execution = await db.scalar(
        select(AutomationExecution)
        .join(AutomationWebhookReceipt, AutomationWebhookReceipt.execution_id == AutomationExecution.id)
        .where(
            AutomationWebhookReceipt.webhook_id == webhook.id,
            AutomationExecution.public_id == execution_id,
        )
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    summary = execution.result_summary or {}
    return {
        "execution_id": execution.public_id,
        "status": execution.status,
        "queued_at": execution.queued_at,
        "started_at": execution.started_at,
        "finished_at": execution.finished_at,
        "summary": summary,
        "error_code": execution.error_code,
        "error_message": execution.error_message,
    }
