"""Notification channel configuration and delivery audit APIs."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.deps.project_context import get_active_project_id, get_active_project_id_member
from fastapi_backend.models.autotest import AutomationNotificationChannel, AutomationNotificationDelivery
from fastapi_backend.models.models import User
from fastapi_backend.services.automation_notification_outbox import (
    _deliver,
    public_channel,
    validate_channel_config,
)
from fastapi_backend.utils.encryption import decrypt, encrypt

router = APIRouter(prefix="/api/auto-test/notification-channels", tags=["自动化通知渠道"])


def _require_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def _channel_body(body: dict[str, Any]) -> tuple[str, str, dict[str, Any], list[str], bool]:
    name = str(body.get("name") or "").strip()[:120]
    channel_type = str(body.get("channel_type") or "").strip().lower()
    if not name:
        raise HTTPException(status_code=422, detail="请填写通知渠道名称")
    try:
        config = validate_channel_config(channel_type, body.get("config") or {})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    notify_on = body.get("notify_on") or ["failed", "timed_out", "infra_error"]
    allowed = {"passed", "failed", "timed_out", "infra_error", "cancelled"}
    if not isinstance(notify_on, list) or not notify_on or any(value not in allowed for value in notify_on):
        raise HTTPException(status_code=422, detail="通知状态配置不正确")
    active = body.get("is_active", True)
    if not isinstance(active, bool):
        raise HTTPException(status_code=422, detail="is_active 必须为布尔值")
    return name, channel_type, config, list(dict.fromkeys(notify_on)), active


@router.get("")
async def list_channels(
    current_user: User = Depends(_require_user),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id),
):
    channels = list(
        (
            await db.scalars(
                select(AutomationNotificationChannel)
                .where(
                    AutomationNotificationChannel.user_id == current_user.id,
                    AutomationNotificationChannel.project_id == project_id,
                )
                .order_by(AutomationNotificationChannel.updated_at.desc())
            )
        ).all()
    )
    return {"channels": [public_channel(channel) for channel in channels]}


@router.post("", status_code=201)
async def create_channel(
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(_require_user),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id_member),
):
    name, channel_type, config, notify_on, active = _channel_body(body)
    duplicate = await db.scalar(
        select(AutomationNotificationChannel).where(
            AutomationNotificationChannel.user_id == current_user.id,
            AutomationNotificationChannel.project_id == project_id,
            AutomationNotificationChannel.name == name,
        )
    )
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="同名通知渠道已存在")
    channel = AutomationNotificationChannel(
        user_id=current_user.id,
        project_id=project_id,
        name=name,
        channel_type=channel_type,
        config_encrypted=encrypt(json.dumps(config, ensure_ascii=False)),
        notify_on=notify_on,
        is_active=active,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return public_channel(channel)


@router.put("/{channel_id}")
async def update_channel(
    channel_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(_require_user),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id_member),
):
    channel = await db.scalar(
        select(AutomationNotificationChannel).where(
            AutomationNotificationChannel.id == channel_id,
            AutomationNotificationChannel.user_id == current_user.id,
            AutomationNotificationChannel.project_id == project_id,
        )
    )
    if channel is None:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    # UI never receives encrypted robot addresses.  An empty URL therefore
    # means "keep the saved destination", not "erase the secret".
    incoming = dict(body)
    raw_config = dict(incoming.get("config") or {})
    if channel.channel_type != "email" and not str(raw_config.get("webhook_url") or "").strip():
        try:
            saved = json.loads(decrypt(channel.config_encrypted))
        except Exception as exc:
            raise HTTPException(status_code=409, detail="原通知配置无法解密，请重新填写通知地址") from exc
        raw_config["webhook_url"] = saved.get("webhook_url", "")
        if not str(raw_config.get("secret") or "").strip() and saved.get("secret"):
            raw_config["secret"] = saved["secret"]
        incoming["config"] = raw_config
        body = incoming
    name, channel_type, config, notify_on, active = _channel_body(body)
    channel.name = name
    channel.channel_type = channel_type
    channel.config_encrypted = encrypt(json.dumps(config, ensure_ascii=False))
    channel.notify_on = notify_on
    channel.is_active = active
    await db.commit()
    await db.refresh(channel)
    return public_channel(channel)


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    current_user: User = Depends(_require_user),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id_member),
):
    channel = await db.scalar(
        select(AutomationNotificationChannel).where(
            AutomationNotificationChannel.id == channel_id,
            AutomationNotificationChannel.user_id == current_user.id,
            AutomationNotificationChannel.project_id == project_id,
        )
    )
    if channel is None:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    await db.delete(channel)
    await db.commit()
    return {"message": "通知渠道已删除"}


@router.post("/{channel_id}/test")
async def test_channel(
    channel_id: str,
    current_user: User = Depends(_require_user),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id_member),
):
    channel = await db.scalar(
        select(AutomationNotificationChannel).where(
            AutomationNotificationChannel.id == channel_id,
            AutomationNotificationChannel.user_id == current_user.id,
            AutomationNotificationChannel.project_id == project_id,
        )
    )
    if channel is None:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    ok, detail = await _deliver(
        channel,
        {
            "execution_id": "TEST-NOTIFICATION",
            "execution_type": "test",
            "target_type": "notification",
            "target_id": 0,
            "status": "passed",
            "attempt": 1,
            "passed": 1,
            "failed": 0,
            "timed_out": 0,
            "cancelled": 0,
            "total": 1,
            "duration_ms": 0,
            "error_code": "",
            "error_message": "",
        },
    )
    if not ok:
        raise HTTPException(status_code=502, detail=f"测试通知发送失败：{detail}")
    return {"message": "测试通知已发送", "detail": detail}


@router.get("/deliveries/history")
async def list_delivery_history(
    limit: int = 100,
    current_user: User = Depends(_require_user),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id),
):
    deliveries = list(
        (
            await db.scalars(
                select(AutomationNotificationDelivery)
                .where(
                    AutomationNotificationDelivery.user_id == current_user.id,
                    AutomationNotificationDelivery.project_id == project_id,
                )
                .order_by(AutomationNotificationDelivery.created_at.desc())
                .limit(min(max(limit, 1), 200))
            )
        ).all()
    )
    return {
        "deliveries": [
            {
                "id": row.id,
                "execution_id": row.execution_id,
                "channel_id": row.channel_id,
                "channel_type": row.channel_type,
                "status": row.status,
                "attempts": row.attempts,
                "next_attempt_at": row.next_attempt_at,
                "delivered_at": row.delivered_at,
                "last_error": row.last_error,
                "payload": row.payload_redacted,
                "created_at": row.created_at,
            }
            for row in deliveries
        ]
    }
