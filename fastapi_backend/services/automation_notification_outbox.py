"""Reliable external result notifications for durable automation executions.

External providers are intentionally handled from a persistent outbox.  A
temporary DingTalk/SMTP outage must not make a completed test look lost, nor
should a process restart silently discard a mobile notification.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import AsyncSessionLocal
from fastapi_backend.core.ssrf_guard import validate_url_safety
from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationNotificationChannel,
    AutomationNotificationDelivery,
    ExecutionEvent,
)
from fastapi_backend.services.autotest_email_notifier import get_email_notifier
from fastapi_backend.utils.encryption import DecryptionError, decrypt

_logger = logging.getLogger(__name__)
_DELIVERY_LOOP_SECONDS = 15
_MAX_ATTEMPTS = 5
_delivery_task: asyncio.Task | None = None
_delivery_tasks: set[asyncio.Task] = set()
_VALID_TYPES = {"dingtalk", "wecom", "feishu", "email", "webhook"}
_VALID_STATUSES = {"passed", "failed", "timed_out", "infra_error", "cancelled"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _redacted_payload(execution: AutomationExecution, context: dict[str, Any]) -> dict[str, Any]:
    summary = dict(execution.result_summary or {})
    status = str(context.get("status") or execution.status)
    return {
        "title": "TestMaster 自动化任务结果",
        "project_id": execution.project_id,
        "execution_id": execution.public_id,
        "execution_type": execution.execution_type,
        "target_type": execution.target_type,
        "target_id": execution.target_id,
        "status": status,
        "attempt": execution.attempt,
        "passed": int(context.get("passed", summary.get("passed", 0)) or 0),
        "failed": int(context.get("failed", summary.get("failed", 0)) or 0),
        "timed_out": int(context.get("timed_out", summary.get("timed_out", 0)) or 0),
        "cancelled": int(context.get("cancelled", summary.get("cancelled", 0)) or 0),
        "total": int(context.get("total", summary.get("total", 0)) or 0),
        "duration_ms": int(context.get("duration_ms", summary.get("duration_ms", 0)) or 0),
        "error_code": execution.error_code or "",
        "error_message": (execution.error_message or "")[:500],
        "finished_at": execution.finished_at.isoformat() if execution.finished_at else None,
    }


def _message(payload: dict[str, Any]) -> str:
    label = {
        "passed": "通过", "failed": "失败", "timed_out": "超时",
        "infra_error": "执行器异常", "cancelled": "已取消",
    }.get(payload["status"], payload["status"])
    lines = [
        "【TestMaster】自动化任务结果",
        f"任务：{payload['execution_id']}",
        f"结果：{label}",
        f"目标：{payload['target_type']} #{payload['target_id']}，第 {payload['attempt']} 次执行",
        f"统计：通过 {payload['passed']}，失败 {payload['failed']}，超时 {payload['timed_out']}，取消 {payload['cancelled']}，共 {payload['total']}",
        f"耗时：{payload['duration_ms']} ms",
    ]
    if payload.get("error_message"):
        lines.append(f"错误：{payload['error_message']}")
    return "\n".join(lines)


def validate_channel_config(channel_type: str, config: dict[str, Any]) -> dict[str, Any]:
    channel_type = str(channel_type or "").strip().lower()
    if channel_type not in _VALID_TYPES:
        raise ValueError("通知渠道仅支持钉钉、企业微信、飞书、邮件或通用 Webhook")
    if not isinstance(config, dict):
        raise ValueError("通知配置必须是对象")
    if channel_type == "email":
        recipients = config.get("recipients")
        if isinstance(recipients, str):
            recipients = [item.strip() for item in recipients.split(",") if item.strip()]
        if not isinstance(recipients, list) or not recipients or len(recipients) > 20:
            raise ValueError("请填写 1 至 20 个邮件收件人")
        normalized = []
        for value in recipients:
            address = str(value).strip()
            if "@" not in address or len(address) > 254:
                raise ValueError("邮件收件人格式不正确")
            normalized.append(address)
        return {"recipients": normalized}
    url = str(config.get("webhook_url") or "").strip()
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("机器人和通用 Webhook 必须使用 HTTPS 地址")
    # Notification destinations are always external.  Do not inherit the
    # request-debugger's development escape hatch: otherwise a saved robot
    # configuration can become a durable SSRF primitive after deployment.
    try:
        address = ipaddress.ip_address(parsed.hostname)
        if not address.is_global:
            raise ValueError("通知地址不安全：不允许回环、私网或保留地址")
    except ValueError as exc:
        if str(exc).startswith("通知地址不安全"):
            raise
    ok, reason = validate_url_safety(url)
    if not ok:
        raise ValueError(f"通知地址不安全：{reason}")
    result = {"webhook_url": url}
    if channel_type == "dingtalk" and str(config.get("secret") or "").strip():
        result["secret"] = str(config["secret"]).strip()
    return result


def public_channel(channel: AutomationNotificationChannel) -> dict[str, Any]:
    try:
        config = json.loads(decrypt(channel.config_encrypted))
    except (DecryptionError, json.JSONDecodeError):
        config = {}
    destination = ""
    if channel.channel_type == "email":
        destination = "、".join(config.get("recipients") or [])
    else:
        destination = urlsplit(str(config.get("webhook_url") or "")).hostname or ""
    return {
        "id": channel.id, "name": channel.name, "channel_type": channel.channel_type,
        "project_id": channel.project_id,
        "notify_on": channel.notify_on or [], "is_active": channel.is_active,
        "destination": destination, "configured": bool(config),
        "created_at": channel.created_at, "updated_at": channel.updated_at,
    }


async def queue_execution_notifications(
    db: AsyncSession, execution: AutomationExecution, context: dict[str, Any] | None = None
) -> int:
    """Write result deliveries in the same transaction as the terminal state."""
    context = context or {}
    payload = _redacted_payload(execution, context)
    if payload["status"] not in _VALID_STATUSES or execution.user_id is None:
        return 0
    channels = list((await db.scalars(select(AutomationNotificationChannel).where(
        AutomationNotificationChannel.user_id == execution.user_id,
        AutomationNotificationChannel.project_id == execution.project_id,
        AutomationNotificationChannel.is_active.is_(True),
    ))).all())
    queued = 0
    for channel in channels:
        if payload["status"] not in (channel.notify_on or ["failed", "timed_out", "infra_error"]):
            continue
        event_key = f"execution:{execution.public_id}:result:{channel.id}:{payload['status']}"
        existing = await db.scalar(select(AutomationNotificationDelivery.id).where(
            AutomationNotificationDelivery.event_key == event_key
        ))
        if existing is not None:
            continue
        db.add(AutomationNotificationDelivery(
            execution_id=execution.id, user_id=execution.user_id,
            project_id=execution.project_id, channel_id=channel.id,
            event_key=event_key, channel_type=channel.channel_type, payload_redacted=payload,
            status="queued", next_attempt_at=_utcnow(),
        ))
        queued += 1
    return queued


def _dingtalk_url(url: str, secret: str | None) -> str:
    if not secret:
        return url
    timestamp = str(int(time.time() * 1000))
    signature = base64.b64encode(hmac.new(secret.encode(), f"{timestamp}\n{secret}".encode(), hashlib.sha256).digest()).decode()
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({"timestamp": timestamp, "sign": signature})
    return urlunsplit(parts._replace(query=urlencode(query)))


async def _deliver(channel: AutomationNotificationChannel, payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        config = json.loads(decrypt(channel.config_encrypted))
    except (DecryptionError, json.JSONDecodeError):
        return False, "通知配置无法解密"
    text = _message(payload)
    if channel.channel_type == "email":
        notifier = get_email_notifier()
        results = [await notifier.send_plain_result(address, "TestMaster 自动化任务结果", text) for address in config.get("recipients") or []]
        return all(results), "邮件已投递" if all(results) else "SMTP 投递失败，请检查邮件服务配置"
    url = str(config.get("webhook_url") or "")
    if channel.channel_type == "dingtalk":
        body = {"msgtype": "text", "text": {"content": text}}
        url = _dingtalk_url(url, config.get("secret"))
    elif channel.channel_type == "wecom":
        body = {"msgtype": "markdown", "markdown": {"content": text}}
    elif channel.channel_type == "feishu":
        body = {"msg_type": "text", "content": {"text": text}}
    else:
        body = {"event": "automation.execution.finished", "data": payload}
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            response = await client.post(url, json=body, headers={"Content-Type": "application/json"})
        if response.status_code >= 300:
            return False, f"HTTP {response.status_code}: {response.text[:300]}"
        try:
            parsed = response.json()
            if isinstance(parsed, dict) and parsed.get("errcode", parsed.get("code", 0)) not in (0, None):
                return False, json.dumps(parsed, ensure_ascii=False)[:300]
        except ValueError:
            pass
        return True, "已投递"
    except httpx.HTTPError as exc:
        return False, str(exc)[:300]


async def deliver_due_notifications(limit: int = 30) -> int:
    """Attempt due rows once.  A restart simply picks up rows left queued."""
    now = _utcnow()
    async with AsyncSessionLocal() as db:
        rows = list((await db.scalars(select(AutomationNotificationDelivery).where(
            AutomationNotificationDelivery.status.in_(("queued", "retrying")),
            AutomationNotificationDelivery.next_attempt_at <= now,
        ).order_by(AutomationNotificationDelivery.created_at).limit(limit))).all())
        identities = [row.id for row in rows]
    delivered = 0
    for delivery_id in identities:
        async with AsyncSessionLocal() as db:
            delivery = await db.get(AutomationNotificationDelivery, delivery_id)
            if delivery is None or delivery.status not in {"queued", "retrying"}:
                continue
            channel = await db.get(AutomationNotificationChannel, delivery.channel_id) if delivery.channel_id else None
            if channel is None or not channel.is_active:
                delivery.status = "failed"
                delivery.last_error = "通知渠道不存在或已停用"
                await db.commit()
                continue
            ok, detail = await _deliver(channel, delivery.payload_redacted or {})
            delivery.attempts += 1
            if ok:
                delivery.status = "delivered"
                delivery.delivered_at = _utcnow()
                delivery.last_error = None
                delivered += 1
            elif delivery.attempts >= _MAX_ATTEMPTS:
                delivery.status = "failed"
                delivery.last_error = detail
            else:
                delivery.status = "retrying"
                delivery.last_error = detail
                delivery.next_attempt_at = _utcnow() + timedelta(seconds=min(900, 2 ** delivery.attempts * 30))
            execution = await db.get(AutomationExecution, delivery.execution_id)
            if execution is not None:
                sequence = (await db.scalar(select(ExecutionEvent.sequence).where(
                    ExecutionEvent.execution_id == execution.id
                ).order_by(ExecutionEvent.sequence.desc()).limit(1)) or 0) + 1
                db.add(ExecutionEvent(
                    execution_id=execution.id, sequence=sequence,
                    event_type="notification_delivered" if ok else "notification_retry_scheduled" if delivery.status == "retrying" else "notification_failed",
                    level="info" if ok else "warning",
                    payload_redacted={"channel": channel.name, "channel_type": channel.channel_type, "attempt": delivery.attempts, "detail": detail[:300]},
                ))
            await db.commit()
    return delivered


async def _delivery_loop() -> None:
    while True:
        await asyncio.sleep(_DELIVERY_LOOP_SECONDS)
        try:
            await deliver_due_notifications()
        except Exception:
            _logger.exception("通知出站箱处理失败")


async def start_notification_delivery_worker() -> None:
    global _delivery_task
    await deliver_due_notifications()
    if _delivery_task is None or _delivery_task.done():
        _delivery_task = asyncio.create_task(_delivery_loop(), name="automation-notification-outbox")


async def stop_notification_delivery_worker() -> None:
    global _delivery_task
    if _delivery_task is not None:
        _delivery_task.cancel()
        try:
            await _delivery_task
        except asyncio.CancelledError:
            pass
        _delivery_task = None
