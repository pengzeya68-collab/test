"""API health monitor service — real case/env URL resolution + background worker."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import AsyncSessionLocal
from fastapi_backend.models.feature_upgrades import APIHealthCheckResult, APIHealthMonitor

_logger = logging.getLogger(__name__)
_WORKER_LOOP_SECONDS = 30
_worker_task: asyncio.Task | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _join_url(base: str | None, path: str | None) -> str:
    base = (base or "").strip()
    path = (path or "").strip()
    if not path:
        return base
    if path.startswith(("http://", "https://")):
        return path
    if not base:
        return path
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


class APIHealthService:
    async def list_monitors(self, db: AsyncSession, project_id: int) -> list[APIHealthMonitor]:
        return list(
            (
                await db.scalars(
                    select(APIHealthMonitor)
                    .where(APIHealthMonitor.project_id == project_id)
                    .order_by(APIHealthMonitor.id.desc())
                )
            ).all()
        )

    async def create_monitor(self, db: AsyncSession, project_id: int, payload: dict[str, Any]) -> APIHealthMonitor:
        monitor = APIHealthMonitor(
            project_id=project_id,
            name=str(payload["name"]).strip(),
            case_id=int(payload["case_id"]),
            environment_id=int(payload["environment_id"]),
            interval_seconds=int(payload.get("interval_seconds") or 300),
            timeout_ms=int(payload.get("timeout_ms") or 10000),
            expected_status=int(payload.get("expected_status") or 200),
            max_response_time_ms=payload.get("max_response_time_ms"),
            alert_consecutive_failures=int(payload.get("alert_consecutive_failures") or 3),
            alert_response_time_degradation=payload.get("alert_response_time_degradation"),
            notification_channel_id=payload.get("notification_channel_id"),
            is_active=bool(payload.get("is_active", True)),
        )
        db.add(monitor)
        await db.flush()
        return monitor

    async def update_monitor(self, db: AsyncSession, monitor_id: int, payload: dict[str, Any]) -> APIHealthMonitor:
        monitor = await db.get(APIHealthMonitor, monitor_id)
        if monitor is None:
            raise LookupError("monitor not found")
        for key in (
            "name",
            "case_id",
            "environment_id",
            "interval_seconds",
            "timeout_ms",
            "expected_status",
            "max_response_time_ms",
            "alert_consecutive_failures",
            "alert_response_time_degradation",
            "notification_channel_id",
            "is_active",
        ):
            if key in payload and payload[key] is not None:
                setattr(monitor, key, payload[key])
        await db.flush()
        return monitor

    async def list_results(self, db: AsyncSession, monitor_id: int, limit: int = 50) -> list[APIHealthCheckResult]:
        return list(
            (
                await db.scalars(
                    select(APIHealthCheckResult)
                    .where(APIHealthCheckResult.monitor_id == monitor_id)
                    .order_by(APIHealthCheckResult.checked_at.desc())
                    .limit(max(1, min(limit, 200)))
                )
            ).all()
        )

    async def resolve_request(
        self,
        db: AsyncSession,
        monitor: APIHealthMonitor,
        *,
        url: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        body: Any = None,
    ) -> dict[str, Any]:
        """Resolve the real HTTP target from API case + environment when overrides are absent."""
        if url:
            return {
                "url": url,
                "method": (method or "GET").upper(),
                "headers": headers or {},
                "body": body,
            }

        from fastapi_backend.models.autotest import AutoTestCase, AutoTestEnvironment

        case = await db.get(AutoTestCase, int(monitor.case_id))
        if case is None:
            raise LookupError(f"health monitor case not found: {monitor.case_id}")
        env = await db.get(AutoTestEnvironment, int(monitor.environment_id))
        base = (env.base_url if env else None) or ""
        case_url = str(case.url or "").strip()
        if not case_url:
            raise ValueError(f"case {monitor.case_id} has empty url")
        target = _join_url(base, case_url)
        if not target.startswith(("http://", "https://")):
            raise ValueError(
                f"resolved health URL is not absolute (case={monitor.case_id}, env={monitor.environment_id}): {target}"
            )

        req_headers: dict[str, str] = {}
        if isinstance(case.headers, dict):
            req_headers.update({str(k): str(v) for k, v in case.headers.items() if v is not None})
        if headers:
            req_headers.update(headers)

        req_body = body
        if req_body is None and case.payload is not None and str(case.method or "GET").upper() not in {"GET", "HEAD"}:
            req_body = case.payload

        return {
            "url": target,
            "method": (method or case.method or "GET").upper(),
            "headers": req_headers,
            "body": req_body,
        }

    async def run_check(
        self,
        db: AsyncSession,
        monitor_id: int,
        *,
        url: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        body: Any = None,
    ) -> APIHealthCheckResult:
        monitor = await db.get(APIHealthMonitor, monitor_id)
        if monitor is None:
            raise LookupError("monitor not found")

        started = _utcnow()
        status = "down"
        status_code = None
        error = None
        response_time_ms = None
        target = None
        try:
            request = await self.resolve_request(
                db,
                monitor,
                url=url,
                method=method,
                headers=headers,
                body=body,
            )
            target = request["url"]
            timeout = max(0.5, float(monitor.timeout_ms or 10000) / 1000.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                kwargs: dict[str, Any] = {"headers": request["headers"] or None}
                # Prefer json for dict/list bodies; otherwise send raw content.
                if request["body"] is not None and request["method"] not in {"GET", "HEAD"}:
                    if isinstance(request["body"], (dict, list)):
                        kwargs["json"] = request["body"]
                    else:
                        kwargs["content"] = (
                            request["body"] if isinstance(request["body"], (bytes, str)) else str(request["body"])
                        )
                response = await client.request(request["method"], target, **kwargs)
            status_code = response.status_code
            response_time_ms = int((_utcnow() - started).total_seconds() * 1000)
            ok_status = status_code == int(monitor.expected_status or 200)
            ok_time = monitor.max_response_time_ms is None or response_time_ms <= int(monitor.max_response_time_ms)
            status = "up" if ok_status and ok_time else "degraded" if ok_status else "down"
            if not ok_status:
                error = f"expected status {monitor.expected_status}, got {status_code} ({target})"
            elif not ok_time:
                error = f"response time {response_time_ms}ms exceeds {monitor.max_response_time_ms}ms ({target})"
        except Exception as exc:
            error = f"{exc}" + (f" ({target})" if target else "")
            response_time_ms = int((_utcnow() - started).total_seconds() * 1000)
            status = "down"

        result = APIHealthCheckResult(
            monitor_id=monitor.id,
            status=status,
            response_time_ms=response_time_ms,
            status_code=status_code,
            error_message=error,
            checked_at=_utcnow(),
        )
        db.add(result)
        monitor.last_check_at = result.checked_at
        monitor.last_status = status
        await db.flush()
        return result

    async def due_monitors(self, db: AsyncSession) -> list[APIHealthMonitor]:
        monitors = list((await db.scalars(select(APIHealthMonitor).where(APIHealthMonitor.is_active.is_(True)))).all())
        now = _utcnow()
        due = []
        for monitor in monitors:
            if monitor.last_check_at is None:
                due.append(monitor)
                continue
            last = monitor.last_check_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            elapsed = (now - last).total_seconds()
            if elapsed >= int(monitor.interval_seconds or 300):
                due.append(monitor)
        return due

    async def _claim_monitor(self, db: AsyncSession, monitor_id: int) -> bool:
        """Atomically claim a due monitor for this worker instance.

        Uses optimistic CAS on ``last_check_at``: only one concurrent updater
        advances the stamp into the future claim window, so multi Uvicorn /
        Gunicorn / Celery workers will not double-fire the same check.
        """
        now = _utcnow()
        monitor = await db.get(APIHealthMonitor, monitor_id)
        if monitor is None or not monitor.is_active:
            return False
        last = monitor.last_check_at
        if last is not None:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            # Another worker already claimed / ran within the interval.
            if (now - last).total_seconds() < int(monitor.interval_seconds or 300):
                return False
        # Stamp immediately so competing workers lose the CAS race.
        claim_stamp = now
        previous = monitor.last_check_at
        stmt = (
            update(APIHealthMonitor)
            .where(APIHealthMonitor.id == monitor_id, APIHealthMonitor.is_active.is_(True))
            .values(last_check_at=claim_stamp)
        )
        if previous is None:
            stmt = stmt.where(APIHealthMonitor.last_check_at.is_(None))
        else:
            stmt = stmt.where(APIHealthMonitor.last_check_at == previous)
        result = await db.execute(stmt)
        if result.rowcount != 1:
            await db.rollback()
            return False
        await db.commit()
        return True

    async def run_due_checks(self, session_factory=None) -> int:
        factory = session_factory or AsyncSessionLocal
        ran = 0
        async with factory() as db:
            due = await self.due_monitors(db)
            due_ids = [int(m.id) for m in due]
        for monitor_id in due_ids:
            # Separate short transactions: claim then execute.
            claimed = False
            async with factory() as db:
                try:
                    claimed = await self._claim_monitor(db, monitor_id)
                except Exception:
                    _logger.exception("health claim failed for monitor %s", monitor_id)
                    try:
                        await db.rollback()
                    except Exception:
                        pass
                    claimed = False
            if not claimed:
                continue
            async with factory() as db:
                try:
                    await self.run_check(db, monitor_id)
                    await db.commit()
                    ran += 1
                except Exception:
                    _logger.exception("health check failed for monitor %s", monitor_id)
                    try:
                        monitor = await db.get(APIHealthMonitor, monitor_id)
                        if monitor is not None:
                            monitor.last_check_at = _utcnow()
                            monitor.last_status = "down"
                            await db.commit()
                    except Exception:
                        _logger.exception("failed to stamp monitor %s after error", monitor_id)
                        try:
                            await db.rollback()
                        except Exception:
                            pass
        return ran


api_health_service = APIHealthService()


async def _health_loop() -> None:
    while True:
        await asyncio.sleep(_WORKER_LOOP_SECONDS)
        try:
            await api_health_service.run_due_checks()
        except Exception:
            _logger.exception("API health worker loop failed")


async def start_api_health_worker() -> None:
    """Start background due-monitor polling (idempotent)."""
    global _worker_task
    try:
        await api_health_service.run_due_checks()
    except Exception:
        _logger.exception("initial API health sweep failed")
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_health_loop(), name="api-health-worker")


async def stop_api_health_worker() -> None:
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
