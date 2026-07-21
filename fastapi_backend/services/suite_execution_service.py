"""Persistent execution runner for scenario regression suites."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update

from fastapi_backend.core.database import AsyncSessionLocal
from fastapi_backend.core.config import settings
from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationExecutionItem,
    ExecutionEvent,
)
from fastapi_backend.services.autotest_scenario_runner import run_scenario

_logger = logging.getLogger(__name__)
_WATCHDOG_INTERVAL_SECONDS = 60
_STALE_HEARTBEAT_SECONDS = max(60, int(os.getenv("TESTMASTER_SUITE_HEARTBEAT_TIMEOUT_SECONDS", "900")))
_HEARTBEAT_INTERVAL_SECONDS = min(30, max(5, _STALE_HEARTBEAT_SECONDS // 3))
_watchdog_task: asyncio.Task | None = None
_inprocess_execution_tasks: set[asyncio.Task] = set()
_execution_heartbeat_tasks: set[asyncio.Task] = set()
_DEFAULT_EXECUTION_TIMEOUT_SECONDS = 1800
_DEFAULT_MAX_RETRIES = 0


async def _append_event(
    db,
    execution_id: int,
    event_type: str,
    payload: dict | None = None,
    level: str = "info",
) -> None:
    sequence = (
        await db.scalar(
            select(func.coalesce(func.max(ExecutionEvent.sequence), 0)).where(
                ExecutionEvent.execution_id == execution_id
            )
        )
    ) + 1
    db.add(
        ExecutionEvent(
            execution_id=execution_id,
            sequence=sequence,
            level=level,
            event_type=event_type,
            payload_redacted=payload or {},
        )
    )


async def reconcile_stale_suite_executions() -> int:
    """Recover abandoned workers and re-dispatch durable queued executions."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=_STALE_HEARTBEAT_SECONDS)
    recovery_dispatch_ids: list[int] = []
    async with AsyncSessionLocal() as db:
        stale = list(
            (
                await db.scalars(
                    select(AutomationExecution).where(
                        AutomationExecution.status.in_(("running", "cancel_requested")),
                        func.coalesce(
                            AutomationExecution.heartbeat_at,
                            AutomationExecution.started_at,
                            AutomationExecution.queued_at,
                        )
                        < cutoff,
                    )
                )
            ).all()
        )
        now = datetime.now(timezone.utc)
        for execution in stale:
            execution.status = "infra_error"
            execution.error_code = "RUNNER_HEARTBEAT_EXPIRED"
            execution.error_message = "执行器心跳超时，任务已由看门狗结束。"
            execution.finished_at = now
            execution.heartbeat_at = now
            pending_items = list(
                (
                    await db.scalars(
                        select(AutomationExecutionItem).where(
                            AutomationExecutionItem.execution_id == execution.id,
                            AutomationExecutionItem.status.in_(("queued", "running")),
                        )
                    )
                ).all()
            )
            for item in pending_items:
                item.status = "infra_error"
                item.error_message = "执行器心跳超时"
                item.finished_at = now
            await _append_event(
                db,
                execution.id,
                "execution_infrastructure_error",
                {"error_code": execution.error_code, "timeout_seconds": _STALE_HEARTBEAT_SECONDS},
                "error",
            )
        queued = list(
            (
                await db.scalars(
                    select(AutomationExecution).where(
                        AutomationExecution.status == "queued",
                        func.coalesce(
                            AutomationExecution.heartbeat_at,
                            AutomationExecution.queued_at,
                        )
                        < cutoff,
                    )
                )
            ).all()
        )
        for execution in queued:
            execution.heartbeat_at = now
            metadata = dict(execution.result_summary or {})
            metadata["last_recovery_dispatch_at"] = now.isoformat()
            execution.result_summary = metadata
            await _append_event(
                db,
                execution.id,
                "execution_recovery_dispatch",
                {"reason": "queued_dispatch_timeout", "timeout_seconds": _STALE_HEARTBEAT_SECONDS},
                "warning",
            )
            recovery_dispatch_ids.append(execution.id)
        if stale or queued:
            await db.commit()
    if stale:
        _logger.warning("Marked %s stale suite executions as infrastructure errors", len(stale))
    for execution_id in recovery_dispatch_ids:
        try:
            await dispatch_suite_execution(execution_id)
        except Exception:
            _logger.exception("Unable to recover queued suite execution %s", execution_id)
    return len(stale) + len(recovery_dispatch_ids)


async def _watchdog_loop() -> None:
    try:
        while True:
            await asyncio.sleep(_WATCHDOG_INTERVAL_SECONDS)
            try:
                await reconcile_stale_suite_executions()
            except Exception:
                # A transient database/broker outage must not permanently stop
                # the process-level reconciliation task.
                _logger.exception("Suite execution watchdog iteration failed")
    except asyncio.CancelledError:
        raise


async def _maintain_execution_heartbeat(execution_id: int, timeout_seconds: int) -> None:
    """Keep a claimed execution live while one scenario legitimately runs for a long time."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        await asyncio.sleep(min(_HEARTBEAT_INTERVAL_SECONDS, remaining))
        async with AsyncSessionLocal() as db:
            touched = await db.execute(
                update(AutomationExecution)
                .where(
                    AutomationExecution.id == execution_id,
                    AutomationExecution.status.in_(("running", "cancel_requested")),
                )
                .values(heartbeat_at=datetime.now(timezone.utc))
            )
            await db.commit()
        if touched.rowcount != 1:
            return


def _start_execution_heartbeat(execution_id: int, timeout_seconds: int) -> None:
    task = asyncio.create_task(
        _maintain_execution_heartbeat(execution_id, timeout_seconds),
        name=f"suite-execution-heartbeat-{execution_id}",
    )
    _execution_heartbeat_tasks.add(task)

    def _discard_heartbeat_task(done_task: asyncio.Task) -> None:
        _execution_heartbeat_tasks.discard(done_task)
        if done_task.cancelled():
            return
        try:
            error = done_task.exception()
        except asyncio.CancelledError:
            return
        if error is not None:
            _logger.exception("Suite execution heartbeat failed", exc_info=error)

    task.add_done_callback(_discard_heartbeat_task)


async def start_suite_execution_watchdog() -> None:
    global _watchdog_task
    await reconcile_stale_suite_executions()
    if _watchdog_task is None or _watchdog_task.done():
        _watchdog_task = asyncio.create_task(_watchdog_loop(), name="suite-execution-watchdog")


async def stop_suite_execution_watchdog() -> None:
    global _watchdog_task
    if _watchdog_task is None:
        return
    _watchdog_task.cancel()
    try:
        await _watchdog_task
    except asyncio.CancelledError:
        pass
    _watchdog_task = None


async def dispatch_suite_execution(execution_id: int) -> None:
    """Send an execution to Celery in production or retain its local task in development."""
    if settings.ENVIRONMENT == "production" and (settings.CELERY_BROKER_URL or settings.REDIS_URL):
        from fastapi_backend.tasks import task_run_suite_execution

        task_run_suite_execution.delay(execution_id)
        return
    task = asyncio.create_task(run_suite_execution(execution_id, runner_id="inprocess-development"))
    _inprocess_execution_tasks.add(task)

    def _discard_finished_task(done_task: asyncio.Task) -> None:
        _inprocess_execution_tasks.discard(done_task)
        try:
            done_task.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            _logger.exception("In-process suite execution failed")

    task.add_done_callback(_discard_finished_task)


def _execution_policy(execution: AutomationExecution) -> tuple[int, int, str, dict]:
    metadata = dict(execution.result_summary or {})
    try:
        timeout_seconds = int(metadata.get("execution_timeout_seconds", _DEFAULT_EXECUTION_TIMEOUT_SECONDS))
    except (TypeError, ValueError):
        timeout_seconds = _DEFAULT_EXECUTION_TIMEOUT_SECONDS
    try:
        max_retries = int(metadata.get("max_retries", _DEFAULT_MAX_RETRIES))
    except (TypeError, ValueError):
        max_retries = _DEFAULT_MAX_RETRIES
    timeout_seconds = min(max(timeout_seconds, 30), 86400)
    max_retries = min(max(max_retries, 0), 5)
    root_key = str(metadata.get("retry_root_key") or "").strip()
    if not root_key:
        root_key = "retry:" + hashlib.sha256(execution.idempotency_key.encode("utf-8")).hexdigest()
    return timeout_seconds, max_retries, root_key[:110], metadata


async def _queue_retry_execution(
    db,
    execution: AutomationExecution,
    metadata: dict,
    root_key: str,
    max_retries: int,
) -> int | None:
    """Create a distinct retry attempt without overwriting its failed parent."""
    if execution.status not in {"failed", "timed_out"} or execution.attempt > max_retries:
        return None
    next_attempt = execution.attempt + 1
    idempotency_key = f"{root_key}:attempt:{next_attempt}"
    existing = await db.scalar(
        select(AutomationExecution).where(AutomationExecution.idempotency_key == idempotency_key)
    )
    if existing is not None:
        return existing.id if existing.status == "queued" else None

    items = list(
        (
            await db.scalars(
                select(AutomationExecutionItem)
                .where(AutomationExecutionItem.execution_id == execution.id)
                .order_by(AutomationExecutionItem.sequence)
            )
        ).all()
    )
    retry_metadata = {
        key: value
        for key, value in metadata.items()
        if key
        in {
            "trigger",
            "schedule_id",
            "webhook_id",
            "execution_timeout_seconds",
            "max_retries",
            "retry_root_key",
            "notification_config",
        }
    }
    retry_metadata.update(
        {
            "retry_root_key": root_key,
            "retry_of_execution_id": execution.public_id,
            "retry_reason": execution.status,
        }
    )
    retry = AutomationExecution(
        execution_type=execution.execution_type,
        target_type=execution.target_type,
        target_id=execution.target_id,
        user_id=execution.user_id,
        env_id=execution.env_id,
        status="queued",
        attempt=next_attempt,
        idempotency_key=idempotency_key,
        result_summary=retry_metadata,
    )
    db.add(retry)
    await db.flush()
    db.add_all(
        AutomationExecutionItem(
            execution_id=retry.id,
            sequence=item.sequence,
            target_type=item.target_type,
            target_id=item.target_id,
            target_name=item.target_name,
            status="queued",
        )
        for item in items
    )
    db.add(
        ExecutionEvent(
            execution_id=retry.id,
            sequence=1,
            event_type="execution_queued",
            payload_redacted={
                "trigger": retry_metadata.get("trigger", "retry"),
                "retry_of_execution_id": execution.public_id,
                "attempt": next_attempt,
                "idempotency_key": idempotency_key,
            },
        )
    )
    await _append_event(
        db,
        execution.id,
        "execution_retry_queued",
        {"retry_execution_id": retry.public_id, "attempt": next_attempt},
        "warning",
    )
    return retry.id


async def _notify_execution_result(execution_id: int, context: dict) -> None:
    from fastapi_backend.services.suite_schedule_service import notification_config_runtime

    config = notification_config_runtime(context.get("notification_config") or {})
    status = str(context.get("status") or "")
    if not config.get("enabled", True) or status not in (config.get("notify_on") or []):
        return
    from fastapi_backend.services.webhook_notify import send_bot_webhook_async

    text = "\n".join(
        [
            "【TestMaster】接口套件执行结果",
            f"套件 ID：{context.get('suite_id')}",
            f"执行编号：{context.get('public_id')}",
            f"结果：{status}",
            f"尝试次数：{context.get('attempt')}",
            f"场景：通过 {context.get('passed', 0)}，失败 {context.get('failed', 0)}，超时 {context.get('timed_out', 0)}，取消 {context.get('cancelled', 0)}",
            f"耗时：{context.get('duration_ms', 0)} ms",
        ]
    )
    ok, detail = await send_bot_webhook_async(config["webhook_url"], text)
    async with AsyncSessionLocal() as db:
        execution = await db.get(AutomationExecution, execution_id)
        if execution is None:
            return
        await _append_event(
            db,
            execution_id,
            "notification_delivered" if ok else "notification_failed",
            {"provider": "bot_webhook", "status": status, "detail": detail[:500]},
            "info" if ok else "warning",
        )
        await db.commit()


async def run_suite_execution(execution_id: int, runner_id: str = "server") -> None:
    """Run one persisted suite execution. Safe to invoke repeatedly."""

    async with AsyncSessionLocal() as db:
        started_at = datetime.now(timezone.utc)
        claimed = await db.execute(
            update(AutomationExecution)
            .where(
                AutomationExecution.id == execution_id,
                AutomationExecution.status == "queued",
            )
            .values(
                status="running",
                runner_id=runner_id,
                started_at=started_at,
                heartbeat_at=started_at,
            )
        )
        if claimed.rowcount != 1:
            return
        execution = await db.get(AutomationExecution, execution_id)
        if execution is None:
            await db.rollback()
            _logger.warning("Suite execution %s disappeared while being claimed", execution_id)
            return
        timeout_seconds, max_retries, root_key, metadata = _execution_policy(execution)
        metadata.update(
            {
                "execution_timeout_seconds": timeout_seconds,
                "max_retries": max_retries,
                "retry_root_key": root_key,
            }
        )
        execution.result_summary = metadata
        await _append_event(
            db,
            execution.id,
            "execution_started",
            {
                "runner_id": runner_id,
                "from_status": "queued",
                "to_status": "running",
                "attempt": execution.attempt,
                "idempotency_key": execution.idempotency_key,
                "timeout_seconds": timeout_seconds,
            },
        )
        await db.commit()
        _start_execution_heartbeat(execution_id, timeout_seconds)

    async with AsyncSessionLocal() as db:
        execution = await db.get(AutomationExecution, execution_id)
        if execution is None:
            return
        items = list(
            (
                await db.scalars(
                    select(AutomationExecutionItem)
                    .where(AutomationExecutionItem.execution_id == execution_id)
                    .order_by(AutomationExecutionItem.sequence)
                )
            ).all()
        )

    passed = failed = cancelled = timed_out = 0
    started = time.monotonic()
    deadline = started + timeout_seconds
    for item in items:
        async with AsyncSessionLocal() as db:
            execution = await db.get(AutomationExecution, execution_id)
            current_item = await db.get(AutomationExecutionItem, item.id)
            if execution is None or current_item is None:
                return
            if execution.status == "cancel_requested":
                current_item.status = "cancelled"
                current_item.finished_at = datetime.now(timezone.utc)
                cancelled += 1
                await _append_event(
                    db,
                    execution_id,
                    "execution_cancel_requested",
                    {"before_item": current_item.sequence, "runner_id": runner_id},
                    "warning",
                )
                await db.commit()
                break

            current_item.status = "running"
            current_item.started_at = datetime.now(timezone.utc)
            execution.heartbeat_at = current_item.started_at
            await _append_event(
                db,
                execution_id,
                "item_started",
                {"sequence": current_item.sequence, "scenario_id": current_item.target_id, "runner_id": runner_id},
            )
            await db.commit()

        item_started = time.monotonic()
        try:
            remaining_seconds = deadline - time.monotonic()
            if remaining_seconds <= 0:
                raise asyncio.TimeoutError
            result = await asyncio.wait_for(
                run_scenario(item.target_id, env_id=execution.env_id, user_id=execution.user_id),
                timeout=remaining_seconds,
            )
            success = bool(result.get("success", False))
            status = "passed" if success else "failed"
            summary = {
                "success_steps": int(result.get("success_steps", 0)),
                "failed_steps": int(result.get("failed_steps", 0)),
                "duration_ms": int((time.monotonic() - item_started) * 1000),
            }
        except asyncio.TimeoutError:
            status = "timed_out"
            timed_out += 1
            summary = {
                "duration_ms": int((time.monotonic() - item_started) * 1000),
                "timeout_seconds": timeout_seconds,
            }
            error_message = f"套件总超时（{timeout_seconds} 秒）"
        except Exception as exc:  # The execution history must survive individual scenario failures.
            _logger.exception("Scenario %s failed in suite execution %s", item.target_id, execution_id)
            status = "failed"
            summary = {"duration_ms": int((time.monotonic() - item_started) * 1000)}
            error_message = str(exc)[:2000]
        else:
            error_message = None

        async with AsyncSessionLocal() as db:
            current_item = await db.get(AutomationExecutionItem, item.id)
            execution = await db.get(AutomationExecution, execution_id)
            if current_item is None or execution is None or execution.status == "infra_error":
                return
            current_item.status = status
            current_item.result_summary = summary
            current_item.error_message = error_message
            current_item.finished_at = datetime.now(timezone.utc)
            execution.heartbeat_at = current_item.finished_at
            await _append_event(
                db,
                execution_id,
                "item_finished",
                {"sequence": current_item.sequence, "status": status, **summary},
                "error" if status in {"failed", "timed_out"} else "info",
            )
            await db.commit()

        if status == "passed":
            passed += 1
        elif status == "failed":
            failed += 1
        if status == "timed_out":
            break

    retry_execution_id: int | None = None
    notification_context: dict = {}
    async with AsyncSessionLocal() as db:
        execution = await db.get(AutomationExecution, execution_id)
        if execution is None:
            return
        if execution.status == "infra_error":
            return
        total = len(items)
        if execution.status == "cancel_requested":
            pending_items = list(
                (
                    await db.scalars(
                        select(AutomationExecutionItem).where(
                            AutomationExecutionItem.execution_id == execution_id,
                            AutomationExecutionItem.status == "queued",
                        )
                    )
                ).all()
            )
            cancelled += len(pending_items)
            now = datetime.now(timezone.utc)
            for pending_item in pending_items:
                pending_item.status = "cancelled"
                pending_item.error_message = "执行已取消"
                pending_item.finished_at = now
        elif timed_out:
            pending_items = list(
                (
                    await db.scalars(
                        select(AutomationExecutionItem).where(
                            AutomationExecutionItem.execution_id == execution_id,
                            AutomationExecutionItem.status == "queued",
                        )
                    )
                ).all()
            )
            now = datetime.now(timezone.utc)
            for pending_item in pending_items:
                pending_item.status = "skipped"
                pending_item.error_message = "套件执行超时"
                pending_item.finished_at = now
        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "cancelled": cancelled,
            "timed_out": timed_out,
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
        metadata = dict(execution.result_summary or {})
        metadata.update(summary)
        execution.result_summary = metadata
        execution.finished_at = datetime.now(timezone.utc)
        execution.heartbeat_at = execution.finished_at
        if execution.status == "cancel_requested":
            execution.status = "cancelled"
        elif timed_out:
            execution.status = "timed_out"
            execution.error_code = "EXECUTION_TIMEOUT"
            execution.error_message = f"套件总超时（{timeout_seconds} 秒）"
        elif failed:
            execution.status = "failed"
        else:
            execution.status = "passed"
        await _append_event(
            db,
            execution_id,
            "execution_finished",
            {
                "status": execution.status,
                "runner_id": runner_id,
                "attempt": execution.attempt,
                "idempotency_key": execution.idempotency_key,
                **summary,
            },
            "error" if execution.status in {"failed", "timed_out"} else "info",
        )
        retry_execution_id = await _queue_retry_execution(db, execution, metadata, root_key, max_retries)
        notification_context = {
            "notification_config": metadata.get("notification_config") or {},
            "status": execution.status,
            "suite_id": execution.target_id,
            "public_id": execution.public_id,
            "attempt": execution.attempt,
            **summary,
        }
        await db.commit()
    if retry_execution_id is not None:
        try:
            await dispatch_suite_execution(retry_execution_id)
        except Exception:
            _logger.exception("Unable to dispatch retry execution %s", retry_execution_id)
    try:
        await _notify_execution_result(execution_id, notification_context)
    except Exception:
        _logger.exception("Unable to send suite execution notification %s", execution_id)
