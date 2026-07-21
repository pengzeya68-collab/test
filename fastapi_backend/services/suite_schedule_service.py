"""Persistent, lease-protected server scheduling for regression suites."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import AsyncSessionLocal
from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationExecutionItem,
    AutoTestScenario,
    ExecutionEvent,
    TestSuite,
    TestSuiteSchedule,
    TestSuiteScenario,
)
from fastapi_backend.services.autotest_scheduler import get_scheduler
from fastapi_backend.services.suite_execution_service import dispatch_suite_execution
from fastapi_backend.utils.encryption import DecryptionError, decrypt, encrypt

_logger = logging.getLogger(__name__)
_LEASE_SECONDS = 120
_MISFIRE_POLICIES = {"coalesce", "skip"}
DEFAULT_EXECUTION_TIMEOUT_SECONDS = 1800
DEFAULT_MAX_RETRIES = 0
MAX_EXECUTION_TIMEOUT_SECONDS = 86400
MAX_SUITE_RETRIES = 5
_NOTIFICATION_STATUSES = {"passed", "failed", "timed_out", "infra_error", "cancelled"}
_NOTIFICATION_HOSTS = {
    "open.feishu.cn",
    "feishu.cn",
    "larksuite.com",
    "oapi.dingtalk.com",
    "dingtalk.com",
    "qyapi.weixin.qq.com",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _job_id(schedule_id: int) -> str:
    return f"suite-schedule-{schedule_id}"


def _cron_trigger(cron_expression: str, timezone_name: str) -> CronTrigger:
    try:
        timezone_value = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("unknown schedule timezone") from exc
    try:
        return CronTrigger.from_crontab(cron_expression, timezone=timezone_value)
    except ValueError as exc:
        raise ValueError("cron expression must contain five fields") from exc


def validate_schedule_config(
    cron_expression: Any,
    timezone_name: Any,
    misfire_policy: Any = "coalesce",
    max_concurrent: Any = 1,
) -> tuple[str, str, str, int]:
    cron = str(cron_expression or "").strip()
    timezone_value = str(timezone_name or "Asia/Shanghai").strip()
    policy = str(misfire_policy or "coalesce").strip().lower()
    try:
        concurrency = int(max_concurrent)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_concurrent must be an integer") from exc
    if policy not in _MISFIRE_POLICIES:
        raise ValueError("misfire_policy must be coalesce or skip")
    if concurrency < 1 or concurrency > 10:
        raise ValueError("max_concurrent must be between 1 and 10")
    _cron_trigger(cron, timezone_value)
    return cron, timezone_value, policy, concurrency


def validate_execution_policy(timeout_seconds: Any, max_retries: Any) -> tuple[int, int]:
    """Validate the policy persisted with an execution, not just its cron job."""
    try:
        timeout = int(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("execution_timeout_seconds must be an integer") from exc
    try:
        retries = int(max_retries)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_retries must be an integer") from exc
    if not 30 <= timeout <= MAX_EXECUTION_TIMEOUT_SECONDS:
        raise ValueError(f"execution_timeout_seconds must be between 30 and {MAX_EXECUTION_TIMEOUT_SECONDS}")
    if not 0 <= retries <= MAX_SUITE_RETRIES:
        raise ValueError(f"max_retries must be between 0 and {MAX_SUITE_RETRIES}")
    return timeout, retries


def validate_notification_config(value: Any) -> dict[str, Any]:
    if value in (None, {}):
        return {}
    if not isinstance(value, dict):
        raise ValueError("notification_config must be an object")
    webhook_url = str(value.get("webhook_url") or "").strip()
    enabled = value.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("notification_config.enabled must be a boolean")
    parsed = urlsplit(webhook_url)
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("通知机器人地址端口无效") from exc
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or not any(host == allowed or host.endswith("." + allowed) for allowed in _NOTIFICATION_HOSTS)
    ):
        raise ValueError("通知仅支持飞书、钉钉或企业微信的 HTTPS 机器人地址")
    raw_statuses = value.get("notify_on", ["failed", "timed_out", "infra_error"])
    if not isinstance(raw_statuses, list) or not raw_statuses:
        raise ValueError("notification_config.notify_on must be a non-empty list")
    statuses = list(dict.fromkeys(str(item).strip().lower() for item in raw_statuses))
    if any(status not in _NOTIFICATION_STATUSES for status in statuses):
        raise ValueError("notification_config.notify_on contains an unsupported status")
    return {"enabled": enabled, "webhook_url": webhook_url[:2000], "notify_on": statuses}


def protect_notification_config(value: dict[str, Any]) -> dict[str, Any]:
    if not value:
        return {}
    parsed = urlsplit(value["webhook_url"])
    return {
        "enabled": value["enabled"],
        "notify_on": value["notify_on"],
        "webhook_url_encrypted": encrypt(value["webhook_url"]),
        "provider_host": (parsed.hostname or "")[:253],
    }


def notification_config_runtime(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        return {}
    if value.get("webhook_url_encrypted"):
        try:
            webhook_url = decrypt(str(value["webhook_url_encrypted"]))
        except DecryptionError as exc:
            raise RuntimeError("通知机器人密钥无法解密") from exc
        return {
            "enabled": value.get("enabled", True),
            "notify_on": value.get("notify_on") or ["failed", "timed_out", "infra_error"],
            "webhook_url": webhook_url,
        }
    # Backward compatibility for the brief pre-encryption development format.
    return validate_notification_config(value)


def notification_config_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        return {}
    return {
        "enabled": value.get("enabled", True),
        "notify_on": value.get("notify_on") or ["failed", "timed_out", "infra_error"],
        "webhook_configured": bool(value.get("webhook_url_encrypted") or value.get("webhook_url")),
        "provider_host": value.get("provider_host") or (urlsplit(str(value.get("webhook_url") or "")).hostname or ""),
        "webhook_url": "",
    }


def install_suite_schedule_job(schedule: TestSuiteSchedule) -> datetime | None:
    trigger = _cron_trigger(schedule.cron_expression, schedule.timezone_name)
    job = get_scheduler().add_job(
        execute_scheduled_suite,
        trigger=trigger,
        args=[schedule.id],
        id=_job_id(schedule.id),
        name=f"Suite schedule {schedule.suite_id}",
        replace_existing=True,
        coalesce=schedule.misfire_policy == "coalesce",
        misfire_grace_time=300 if schedule.misfire_policy == "coalesce" else 1,
        max_instances=1,
    )
    if not schedule.is_active:
        get_scheduler().pause_job(job.id)
    # APScheduler keeps jobs pending until start() in tests and first-time setup.
    return getattr(job, "next_run_time", None)


def remove_suite_schedule_job(schedule_id: int) -> None:
    try:
        get_scheduler().remove_job(_job_id(schedule_id))
    except JobLookupError:
        pass


def _next_run(schedule_id: int) -> datetime | None:
    job = get_scheduler().get_job(_job_id(schedule_id))
    return job.next_run_time if job else None


async def restore_suite_schedules() -> int:
    """Install DB-backed schedules after APScheduler starts or a process restarts."""
    async with AsyncSessionLocal() as db:
        schedules = list((await db.scalars(select(TestSuiteSchedule))).all())
        restored = 0
        for schedule in schedules:
            try:
                schedule.next_run_at = install_suite_schedule_job(schedule)
                restored += 1
            except Exception:
                _logger.exception("Unable to restore suite schedule %s", schedule.id)
        await db.commit()
        return restored


async def _release_lease(db: AsyncSession, schedule_id: int, lease_token: str) -> None:
    await db.execute(
        update(TestSuiteSchedule)
        .where(TestSuiteSchedule.id == schedule_id, TestSuiteSchedule.lease_token == lease_token)
        .values(lease_token=None, lease_expires_at=None)
    )


async def execute_scheduled_suite(schedule_id: int) -> None:
    """Create one idempotent execution record when this cron occurrence owns the DB lease."""
    now = _utcnow()
    lease_token = uuid.uuid4().hex
    execution_id: int | None = None
    should_dispatch = False
    async with AsyncSessionLocal() as db:
        acquired = await db.execute(
            update(TestSuiteSchedule)
            .where(
                TestSuiteSchedule.id == schedule_id,
                TestSuiteSchedule.is_active.is_(True),
                or_(TestSuiteSchedule.lease_expires_at.is_(None), TestSuiteSchedule.lease_expires_at < now),
            )
            .values(lease_token=lease_token, lease_expires_at=now + timedelta(seconds=_LEASE_SECONDS))
        )
        if acquired.rowcount != 1:
            return
        try:
            schedule = await db.get(TestSuiteSchedule, schedule_id)
            suite = await db.get(TestSuite, schedule.suite_id) if schedule else None
            if schedule is None or suite is None or not suite.is_active:
                return
            occurrence = now.strftime("%Y%m%d%H%M")
            idempotency_key = f"suite-schedule:{schedule.id}:{occurrence}"
            existing = await db.scalar(
                select(AutomationExecution).where(AutomationExecution.idempotency_key == idempotency_key)
            )
            running_count = 0
            if existing is None:
                running_count = (
                    await db.scalar(
                        select(func.count())
                        .select_from(AutomationExecution)
                        .where(
                            AutomationExecution.target_type == "suite",
                            AutomationExecution.target_id == suite.id,
                            AutomationExecution.status.in_(("queued", "running", "cancel_requested")),
                        )
                    )
                    or 0
                )
            if running_count >= schedule.max_concurrent:
                schedule.next_run_at = _next_run(schedule.id)
                return
            members = list(
                (
                    await db.execute(
                        select(TestSuiteScenario, AutoTestScenario)
                        .join(AutoTestScenario, AutoTestScenario.id == TestSuiteScenario.scenario_id)
                        .where(TestSuiteScenario.suite_id == suite.id, AutoTestScenario.is_active.is_(True))
                        .order_by(TestSuiteScenario.sort_order)
                    )
                ).all()
            )
            if not members and existing is None:
                return
            if existing is not None:
                execution_id = existing.id
                # Re-dispatching a queued occurrence closes the gap between a
                # committed execution row and a lost broker message. The
                # runner claims queued work atomically before it can execute.
                should_dispatch = existing.status == "queued"
            else:
                execution = AutomationExecution(
                    execution_type="suite",
                    target_type="suite",
                    target_id=suite.id,
                    user_id=suite.user_id,
                    env_id=schedule.env_id if schedule.env_id is not None else suite.env_id,
                    status="queued",
                    idempotency_key=idempotency_key,
                    result_summary={
                        "trigger": "schedule",
                        "schedule_id": schedule.id,
                        "execution_timeout_seconds": schedule.execution_timeout_seconds,
                        "max_retries": schedule.max_retries,
                        "notification_config": schedule.notification_config or {},
                    },
                )
                db.add(execution)
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
                        payload_redacted={"suite_id": suite.id, "schedule_id": schedule.id, "trigger": "schedule"},
                    )
                )
                execution_id = execution.id
                should_dispatch = True
            schedule.last_enqueued_at = now
            schedule.last_execution_id = execution_id
            schedule.next_run_at = _next_run(schedule.id)
            await db.commit()
        except Exception:
            await db.rollback()
            _logger.exception("Failed to create scheduled suite execution for schedule %s", schedule_id)
            return
        finally:
            try:
                await _release_lease(db, schedule_id, lease_token)
                await db.commit()
            except Exception:
                await db.rollback()
    if execution_id is not None and should_dispatch:
        await dispatch_suite_execution(execution_id)


def schedule_payload(schedule: TestSuiteSchedule) -> dict[str, Any]:
    return {
        "id": schedule.id,
        "suite_id": schedule.suite_id,
        "cron_expression": schedule.cron_expression,
        "timezone_name": schedule.timezone_name,
        "is_active": schedule.is_active,
        "env_id": schedule.env_id,
        "misfire_policy": schedule.misfire_policy,
        "max_concurrent": schedule.max_concurrent,
        "execution_timeout_seconds": schedule.execution_timeout_seconds,
        "max_retries": schedule.max_retries,
        "notification_config": notification_config_payload(schedule.notification_config),
        "next_run_at": schedule.next_run_at,
        "last_enqueued_at": schedule.last_enqueued_at,
        "last_execution_id": schedule.last_execution_id,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
    }
