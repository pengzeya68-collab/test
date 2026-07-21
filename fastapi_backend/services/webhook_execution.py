"""Signed, idempotent external triggers for persisted regression suites."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationExecutionItem,
    AutomationWebhook,
    AutomationWebhookReceipt,
    AutoTestScenario,
    ExecutionEvent,
    TestSuite,
    TestSuiteScenario,
)
from fastapi_backend.utils.encryption import DecryptionError, decrypt, encrypt

_EVENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_MIN_CLOCK_SKEW_SECONDS = 30
_MAX_CLOCK_SKEW_SECONDS = 3600


def generate_webhook_secret() -> str:
    """Generate an opaque secret suitable for HMAC-SHA256 signing."""
    return secrets.token_urlsafe(32)


def normalize_clock_skew(value: Any) -> int:
    try:
        skew = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="允许的时间偏差必须是整数秒") from exc
    if not _MIN_CLOCK_SKEW_SECONDS <= skew <= _MAX_CLOCK_SKEW_SECONDS:
        raise HTTPException(
            status_code=422,
            detail=f"允许的时间偏差必须在 {_MIN_CLOCK_SKEW_SECONDS} 到 {_MAX_CLOCK_SKEW_SECONDS} 秒之间",
        )
    return skew


def normalize_event_id(value: Any) -> str:
    event_id = str(value or "").strip()
    if not _EVENT_ID_RE.fullmatch(event_id):
        raise HTTPException(status_code=422, detail="X-TestMaster-Event-Id 格式不正确")
    return event_id


def sign_webhook_payload(secret: str, timestamp: str, raw_body: bytes) -> str:
    """Return the canonical lower-case digest for ``timestamp + '.' + body``."""
    return hmac.new(
        secret.encode("utf-8"),
        timestamp.encode("ascii") + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()


def _signature_digest(value: Any) -> str:
    signature = str(value or "").strip().lower()
    for prefix in ("sha256=", "v1="):
        if signature.startswith(prefix):
            signature = signature[len(prefix) :]
            break
    if not _HEX_DIGEST_RE.fullmatch(signature):
        raise HTTPException(status_code=401, detail="Webhook 签名格式不正确")
    return signature


def _validate_timestamp(timestamp: Any, allowed_skew_seconds: int, now: float | None = None) -> str:
    raw_timestamp = str(timestamp or "").strip()
    if not raw_timestamp.isascii() or not raw_timestamp.isdecimal():
        raise HTTPException(status_code=401, detail="Webhook 时间戳格式不正确")
    try:
        timestamp_value = int(raw_timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Webhook 时间戳格式不正确") from exc
    current_time = time.time() if now is None else now
    if abs(current_time - timestamp_value) > allowed_skew_seconds:
        raise HTTPException(status_code=401, detail="Webhook 时间戳已过期或超出允许偏差")
    return raw_timestamp


async def authenticate_webhook_request(
    db: AsyncSession,
    webhook_id: str,
    timestamp: Any,
    signature: Any,
    raw_body: bytes,
) -> AutomationWebhook:
    """Load a live webhook and validate its timestamp-bound HMAC signature."""
    webhook = await db.get(AutomationWebhook, webhook_id)
    if webhook is None or not webhook.is_active:
        # Do not reveal whether an inactive credential exists to an unauthenticated caller.
        raise HTTPException(status_code=404, detail="Webhook 不存在或已停用")
    raw_timestamp = _validate_timestamp(timestamp, normalize_clock_skew(webhook.allowed_clock_skew_seconds))
    try:
        secret = decrypt(webhook.signing_secret_encrypted)
    except DecryptionError as exc:
        raise HTTPException(status_code=503, detail="Webhook 密钥当前不可用") from exc
    expected = sign_webhook_payload(secret, raw_timestamp, raw_body)
    if not hmac.compare_digest(expected, _signature_digest(signature)):
        raise HTTPException(status_code=401, detail="Webhook 签名校验失败")
    return webhook


async def create_webhook_execution(
    db: AsyncSession,
    webhook: AutomationWebhook,
    event_id: str,
    raw_body: bytes,
) -> tuple[AutomationExecution, bool]:
    """Atomically persist an external event receipt and its queued execution.

    The receipt's uniqueness constraint is the durable replay barrier. A repeated
    request with the same event and payload returns the original execution. A
    reused event ID with a different payload is rejected instead of silently
    acting on an ambiguous CI event.
    """
    event_id = normalize_event_id(event_id)
    request_sha256 = hashlib.sha256(raw_body).hexdigest()
    receipt = await db.scalar(
        select(AutomationWebhookReceipt).where(
            AutomationWebhookReceipt.webhook_id == webhook.id,
            AutomationWebhookReceipt.event_id == event_id,
        )
    )
    if receipt is not None:
        if not hmac.compare_digest(receipt.request_sha256, request_sha256):
            raise HTTPException(status_code=409, detail="Webhook 事件 ID 已被不同内容使用")
        existing = await db.get(AutomationExecution, receipt.execution_id)
        if existing is None:
            raise HTTPException(status_code=409, detail="Webhook 事件记录不完整，请联系管理员")
        return existing, True

    suite = await db.scalar(
        select(TestSuite).where(TestSuite.id == webhook.suite_id, TestSuite.user_id == webhook.user_id)
    )
    if suite is None or not suite.is_active:
        raise HTTPException(status_code=409, detail="Webhook 关联的测试套件不存在或已停用")
    members = list(
        (
            await db.execute(
                select(TestSuiteScenario, AutoTestScenario)
                .join(AutoTestScenario, AutoTestScenario.id == TestSuiteScenario.scenario_id)
                .where(
                    TestSuiteScenario.suite_id == suite.id,
                    AutoTestScenario.is_active.is_(True),
                )
                .order_by(TestSuiteScenario.sort_order)
            )
        ).all()
    )
    if not members:
        raise HTTPException(status_code=409, detail="Webhook 关联的测试套件没有可执行场景")

    idempotency_key = f"webhook:{webhook.id}:{hashlib.sha256(event_id.encode('utf-8')).hexdigest()}"
    execution = AutomationExecution(
        execution_type="suite",
        target_type="suite",
        target_id=suite.id,
        user_id=webhook.user_id,
        env_id=suite.env_id,
        status="queued",
        idempotency_key=idempotency_key,
        result_summary={"trigger": "webhook", "webhook_id": webhook.id},
    )
    db.add(execution)
    try:
        await db.flush()
        db.add_all(
            AutomationExecutionItem(
                execution_id=execution.id,
                sequence=index,
                target_type="scenario",
                target_id=scenario.id,
                target_name=scenario.name,
                status="queued",
            )
            for index, (_membership, scenario) in enumerate(members)
        )
        db.add(
            ExecutionEvent(
                execution_id=execution.id,
                sequence=1,
                event_type="execution_queued",
                payload_redacted={
                    "suite_id": suite.id,
                    "trigger": "webhook",
                    "webhook_id": webhook.id,
                    "event_id_sha256": hashlib.sha256(event_id.encode("utf-8")).hexdigest(),
                },
            )
        )
        db.add(
            AutomationWebhookReceipt(
                webhook_id=webhook.id,
                event_id=event_id,
                request_sha256=request_sha256,
                execution_id=execution.id,
            )
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        receipt = await db.scalar(
            select(AutomationWebhookReceipt).where(
                AutomationWebhookReceipt.webhook_id == webhook.id,
                AutomationWebhookReceipt.event_id == event_id,
            )
        )
        if receipt is None:
            raise HTTPException(status_code=409, detail="Webhook 幂等事件发生冲突，请使用新的事件 ID")
        if not hmac.compare_digest(receipt.request_sha256, request_sha256):
            raise HTTPException(status_code=409, detail="Webhook 事件 ID 已被不同内容使用")
        existing = await db.get(AutomationExecution, receipt.execution_id)
        if existing is None:
            raise HTTPException(status_code=409, detail="Webhook 事件记录不完整，请联系管理员")
        return existing, True
    await db.refresh(execution)
    return execution, False


def encrypt_webhook_secret(secret: str) -> str:
    return encrypt(secret)
