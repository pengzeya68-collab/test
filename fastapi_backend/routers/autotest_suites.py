"""Database-backed regression suites and asynchronous execution records."""

from __future__ import annotations

import json
import logging
import hashlib
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationExecutionItem,
    AutoTestScenario,
    ExecutionEvent,
    ImportJob,
    TestSuite,
    TestSuiteCase,
    TestSuiteSchedule,
    TestSuiteScenario,
)
from fastapi_backend.models.models import User
from fastapi_backend.services.suite_execution_service import dispatch_suite_execution
from fastapi_backend.services.suite_schedule_service import (
    install_suite_schedule_job,
    notification_config_runtime,
    protect_notification_config,
    remove_suite_schedule_job,
    schedule_payload,
    validate_execution_policy,
    validate_notification_config,
    validate_schedule_config,
)

router = APIRouter(prefix="/api/auto-test/suites", tags=["Regression Suites"])
_logger = logging.getLogger(__name__)
_LEGACY_SUITES_FILE = Path(__file__).parent.parent / "autotest_data" / "suites.json"
_LEGACY_RUNS_FILE = _LEGACY_SUITES_FILE.parent / "runs" / "runs.json"
_LEGACY_MIGRATION_SOURCE = "legacy_suite_json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return _utcnow()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _backup_legacy_source(path: Path) -> dict[str, str]:
    """Create an immutable, content-addressed backup before switching read paths."""
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    backup_dir = path.parent / "legacy-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{path.name}.{digest[:16]}.readonly"
    if not backup_path.exists():
        shutil.copy2(path, backup_path)
        try:
            backup_path.chmod(0o444)
        except OSError:
            # The copy remains a valid backup on filesystems that do not expose
            # POSIX-style read-only bits (such as some Windows configurations).
            pass
    return {"filename": backup_path.name, "sha256": digest, "size_bytes": str(len(content))}


async def _migrate_legacy_suites(db: AsyncSession, user_id: int) -> None:
    """One-time, auditable migration from the retired JSON suite store.

    A completed ImportJob is the cut-over marker. Once present, all callers read
    only database records and never let a later edit to the archived JSON alter
    suite state.
    """
    completed = await db.scalar(
        select(ImportJob.id).where(
            ImportJob.user_id == user_id,
            ImportJob.source_type == _LEGACY_MIGRATION_SOURCE,
            ImportJob.status == "completed",
        )
    )
    if completed is not None or not _LEGACY_SUITES_FILE.exists():
        return

    try:
        legacy_source_text = _LEGACY_SUITES_FILE.read_text(encoding="utf-8")
        if legacy_source_text.strip() in {"", "{}"}:
            return
        suites_backup = _backup_legacy_source(_LEGACY_SUITES_FILE)
        runs_backup = _backup_legacy_source(_LEGACY_RUNS_FILE) if _LEGACY_RUNS_FILE.exists() else None
        legacy_suites = _load_json(_LEGACY_SUITES_FILE)
    except (OSError, UnicodeDecodeError) as exc:
        db.add(
            ImportJob(
                user_id=user_id,
                source_type=_LEGACY_MIGRATION_SOURCE,
                status="failed",
                summary={"sensitive_values_redacted": True, "failure_stage": "backup"},
                error_summary=f"legacy suite backup failed: {type(exc).__name__}",
                completed_at=_utcnow(),
            )
        )
        await db.commit()
        _logger.warning("Legacy suite migration backup failed for user %s", user_id)
        return

    if not legacy_suites:
        db.add(
            ImportJob(
                user_id=user_id,
                source_type=_LEGACY_MIGRATION_SOURCE,
                status="failed",
                summary={"sensitive_values_redacted": True, "failure_stage": "validation", "backup": suites_backup},
                error_summary="legacy suite source is not a JSON object",
                completed_at=_utcnow(),
            )
        )
        await db.commit()
        _logger.warning("Legacy suite source failed validation for user %s", user_id)
        return

    job = ImportJob(
        user_id=user_id,
        source_type=_LEGACY_MIGRATION_SOURCE,
        status="running",
        summary={
            "sensitive_values_redacted": True,
            "suite_backup": suites_backup,
            "run_backup": runs_backup,
            "source_suite_count": len(legacy_suites),
        },
    )
    db.add(job)
    await db.flush()

    legacy_to_suite: dict[str, TestSuite] = {}
    source_suite_count = created_suite_count = expected_memberships = migrated_memberships = 0
    for legacy_id, payload in legacy_suites.items():
        if not isinstance(payload, dict) or payload.get("user_id") != user_id:
            continue
        source_suite_count += 1
        legacy_key = f"legacy-json:{legacy_id}"
        suite = await db.scalar(select(TestSuite).where(TestSuite.legacy_key == legacy_key))
        if suite is None:
            raw_scenario_ids = payload.get("scenario_ids") or []
            scenario_ids = list(dict.fromkeys(item for item in raw_scenario_ids if isinstance(item, int) and item > 0))
            scenarios = (
                list(
                    (
                        await db.scalars(
                            select(AutoTestScenario).where(
                                AutoTestScenario.id.in_(scenario_ids),
                                AutoTestScenario.user_id == user_id,
                            )
                        )
                    ).all()
                )
                if scenario_ids
                else []
            )
            allowed_ids = {scenario.id for scenario in scenarios}
            suite = TestSuite(
                name=str(payload.get("name") or f"Migrated suite {legacy_id}")[:200],
                description=str(payload.get("description") or ""),
                env_id=payload.get("env_id"),
                user_id=user_id,
                kind="scenario",
                legacy_key=legacy_key,
                created_at=_parse_datetime(payload.get("created_at")),
            )
            db.add(suite)
            await db.flush()
            created_suite_count += 1
            for index, scenario_id in enumerate(scenario_ids):
                if scenario_id in allowed_ids:
                    db.add(TestSuiteScenario(suite_id=suite.id, scenario_id=scenario_id, sort_order=index))
                    migrated_memberships += 1
            expected_memberships += len(allowed_ids)
        else:
            expected_memberships += (
                await db.scalar(
                    select(func.count()).select_from(TestSuiteScenario).where(TestSuiteScenario.suite_id == suite.id)
                )
                or 0
            )
            migrated_memberships += (
                await db.scalar(
                    select(func.count()).select_from(TestSuiteScenario).where(TestSuiteScenario.suite_id == suite.id)
                )
                or 0
            )
        legacy_to_suite[str(legacy_id)] = suite

    imported_run_count = 0
    if legacy_to_suite and _LEGACY_RUNS_FILE.exists():
        legacy_runs = _load_json(_LEGACY_RUNS_FILE)
        for legacy_suite_id, runs in legacy_runs.items():
            suite = legacy_to_suite.get(str(legacy_suite_id))
            if suite is None or not isinstance(runs, list):
                continue
            for legacy_run in runs:
                if not isinstance(legacy_run, dict):
                    continue
                legacy_run_id = legacy_run.get("run_id")
                idempotency_key = f"legacy-suite-run:{legacy_suite_id}:{legacy_run_id}"
                existing = await db.scalar(
                    select(AutomationExecution.id).where(AutomationExecution.idempotency_key == idempotency_key)
                )
                if existing is not None:
                    continue
                failed = int(legacy_run.get("failed") or 0)
                execution = AutomationExecution(
                    execution_type="suite",
                    target_type="suite",
                    target_id=suite.id,
                    user_id=user_id,
                    env_id=suite.env_id,
                    status="failed" if failed else "passed",
                    idempotency_key=idempotency_key,
                    runner_id="legacy-json-import",
                    result_summary={
                        "total": int(legacy_run.get("total") or 0),
                        "passed": int(legacy_run.get("passed") or 0),
                        "failed": failed,
                        "skipped": int(legacy_run.get("skipped") or 0),
                        "legacy_run_id": legacy_run_id,
                    },
                    queued_at=_parse_datetime(legacy_run.get("started_at")),
                    started_at=_parse_datetime(legacy_run.get("started_at")),
                    finished_at=_parse_datetime(legacy_run.get("finished_at") or legacy_run.get("started_at")),
                )
                db.add(execution)
                imported_run_count += 1

    job.status = "completed"
    job.completed_at = _utcnow()
    job.summary = {
        **(job.summary or {}),
        "migrated_suite_count": source_suite_count,
        "created_suite_count": created_suite_count,
        "migrated_membership_count": migrated_memberships,
        "expected_membership_count": expected_memberships,
        "imported_run_count": imported_run_count,
        "database_read_path_enabled": True,
    }

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        _logger.info("Legacy suite migration raced with another worker; using existing rows")


async def _suite_or_404(db: AsyncSession, suite_id: int, user_id: int) -> TestSuite:
    suite = await db.scalar(select(TestSuite).where(TestSuite.id == suite_id, TestSuite.user_id == user_id))
    if suite is None:
        raise HTTPException(status_code=404, detail="测试套件不存在或无权访问")
    return suite


async def _suite_scenarios(db: AsyncSession, suite_id: int, executable_only: bool = False) -> list[dict[str, Any]]:
    query = (
        select(TestSuiteScenario, AutoTestScenario)
        .join(AutoTestScenario, AutoTestScenario.id == TestSuiteScenario.scenario_id)
        .where(TestSuiteScenario.suite_id == suite_id)
        .order_by(TestSuiteScenario.sort_order)
    )
    if executable_only:
        query = query.where(AutoTestScenario.is_active.is_(True))
    rows = (await db.execute(query)).all()
    return [
        {
            "id": scenario.id,
            "scenario_id": scenario.id,
            "name": scenario.name,
            "case_name": scenario.name,
            "active": scenario.is_active,
            "sort_order": membership.sort_order,
        }
        for membership, scenario in rows
    ]


async def _execution_payload(db: AsyncSession, execution: AutomationExecution) -> dict[str, Any]:
    items = list(
        (
            await db.scalars(
                select(AutomationExecutionItem)
                .where(AutomationExecutionItem.execution_id == execution.id)
                .order_by(AutomationExecutionItem.sequence)
            )
        ).all()
    )
    summary = execution.result_summary or {}
    return {
        "execution_id": execution.public_id,
        "id": execution.public_id,
        "status": execution.status,
        "attempt": execution.attempt,
        "trigger": summary.get("trigger", "manual"),
        "retry_of_execution_id": summary.get("retry_of_execution_id"),
        "suite_id": execution.target_id,
        "env_id": execution.env_id,
        "total_cases": int(summary.get("total", len(items))),
        "passed_cases": int(summary.get("passed", 0)),
        "failed_cases": int(summary.get("failed", 0)),
        "cancelled_cases": int(summary.get("cancelled", 0)),
        "duration_ms": int(summary.get("duration_ms", 0)),
        "queued_at": execution.queued_at,
        "started_at": execution.started_at,
        "finished_at": execution.finished_at,
        "error_code": execution.error_code,
        "error_message": execution.error_message,
        "summary": summary,
        "case_results": [
            {
                "scenario_id": item.target_id,
                "case_name": item.target_name,
                "status": item.status,
                "duration_ms": int((item.result_summary or {}).get("duration_ms", 0)),
                "error": item.error_message,
                "result": item.result_summary or {},
            }
            for item in items
        ],
    }


async def _suite_payload(db: AsyncSession, suite: TestSuite) -> dict[str, Any]:
    scenarios = await _suite_scenarios(db, suite.id)
    latest = await db.scalar(
        select(AutomationExecution)
        .where(
            AutomationExecution.target_type == "suite",
            AutomationExecution.target_id == suite.id,
        )
        .order_by(AutomationExecution.created_at.desc())
    )
    return {
        "id": suite.id,
        "name": suite.name,
        "description": suite.description or "",
        "env_id": suite.env_id,
        "scenario_ids": [scenario["scenario_id"] for scenario in scenarios],
        "scenarios": scenarios,
        "case_count": len(scenarios),
        "scenario_count": len(scenarios),
        "is_active": suite.is_active,
        "created_at": suite.created_at,
        "updated_at": suite.updated_at,
        "last_status": latest.status if latest else None,
        "last_run_at": latest.finished_at or latest.started_at if latest else None,
    }


async def _validate_scenarios(db: AsyncSession, scenario_ids: list[Any], user_id: int) -> list[int]:
    normalized = []
    for value in scenario_ids:
        try:
            scenario_id = int(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="场景 ID 必须为整数") from exc
        if scenario_id not in normalized:
            normalized.append(scenario_id)
    if not normalized:
        return []
    found_ids = set(
        (
            await db.scalars(
                select(AutoTestScenario.id).where(
                    AutoTestScenario.id.in_(normalized),
                    AutoTestScenario.user_id == user_id,
                )
            )
        ).all()
    )
    missing = [scenario_id for scenario_id in normalized if scenario_id not in found_ids]
    if missing:
        raise HTTPException(status_code=400, detail=f"场景不存在或无权访问: {missing}")
    return normalized


async def _dispatch_execution(execution: AutomationExecution) -> None:
    await dispatch_suite_execution(execution.id)


@router.get("")
async def list_suites(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(require_permissions("suite:read")),
    db: AsyncSession = Depends(get_autotest_db),
):
    await _migrate_legacy_suites(db, current_user.id)
    page = max(page, 1)
    size = min(max(size, 1), 100)
    total = (
        await db.scalar(select(func.count()).select_from(TestSuite).where(TestSuite.user_id == current_user.id)) or 0
    )
    suites = list(
        (
            await db.scalars(
                select(TestSuite)
                .where(TestSuite.user_id == current_user.id)
                .order_by(TestSuite.updated_at.desc(), TestSuite.id.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
    )
    payload = [await _suite_payload(db, suite) for suite in suites]
    return {"list": payload, "suites": payload, "total": total, "page": page, "size": size}


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: User = Depends(require_permissions("execution:read")),
    db: AsyncSession = Depends(get_autotest_db),
):
    execution = await db.scalar(
        select(AutomationExecution).where(
            AutomationExecution.public_id == execution_id,
            AutomationExecution.user_id == current_user.id,
        )
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="执行记录不存在或无权访问")
    return await _execution_payload(db, execution)


@router.get("/executions/{execution_id}/events")
async def list_execution_events(
    execution_id: str,
    after: int = 0,
    limit: int = 200,
    current_user: User = Depends(require_permissions("execution:read")),
    db: AsyncSession = Depends(get_autotest_db),
):
    execution = await db.scalar(
        select(AutomationExecution).where(
            AutomationExecution.public_id == execution_id,
            AutomationExecution.user_id == current_user.id,
        )
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="执行记录不存在或无权访问")
    events = list(
        (
            await db.scalars(
                select(ExecutionEvent)
                .where(ExecutionEvent.execution_id == execution.id, ExecutionEvent.sequence > max(after, 0))
                .order_by(ExecutionEvent.sequence)
                .limit(min(max(limit, 1), 500))
            )
        ).all()
    )
    return {
        "events": [
            {
                "sequence": event.sequence,
                "level": event.level,
                "type": event.event_type,
                "payload": event.payload_redacted or {},
                "created_at": event.created_at,
            }
            for event in events
        ]
    }


@router.post("")
@audit_log("create", "suite")
async def create_suite(
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("suite:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    await _migrate_legacy_suites(db, current_user.id)
    name = str(body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="套件名称不能为空")
    scenario_ids = await _validate_scenarios(db, body.get("scenario_ids") or [], current_user.id)
    suite = TestSuite(
        name=name[:200],
        description=str(body.get("description") or ""),
        env_id=body.get("env_id"),
        user_id=current_user.id,
        kind="scenario",
    )
    db.add(suite)
    await db.flush()
    db.add_all(
        TestSuiteScenario(suite_id=suite.id, scenario_id=scenario_id, sort_order=index)
        for index, scenario_id in enumerate(scenario_ids)
    )
    await db.commit()
    await db.refresh(suite)
    return await _suite_payload(db, suite)


@router.post("/{suite_id}/executions", status_code=status.HTTP_202_ACCEPTED)
@router.post("/{suite_id}/run", status_code=status.HTTP_202_ACCEPTED)
@audit_log("execute", "suite", resource_id_param="suite_id")
async def create_suite_execution(
    suite_id: int,
    body: dict[str, Any] = Body(default_factory=dict),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(require_permissions("suite:execute")),
    db: AsyncSession = Depends(get_autotest_db),
):
    suite = await _suite_or_404(db, suite_id, current_user.id)
    if not suite.is_active:
        raise HTTPException(status_code=409, detail="测试套件已停用，不能执行")
    scenario_rows = await _suite_scenarios(db, suite.id, executable_only=True)
    if not scenario_rows:
        raise HTTPException(status_code=400, detail="测试套件没有可执行场景")
    key = (idempotency_key or f"suite:{suite.id}:{uuid.uuid4().hex}").strip()[:128]
    existing = await db.scalar(select(AutomationExecution).where(AutomationExecution.idempotency_key == key))
    if existing is not None:
        if existing.user_id != current_user.id:
            raise HTTPException(status_code=409, detail="幂等键已被其他用户使用")
        return await _execution_payload(db, existing)

    try:
        timeout_seconds, max_retries = validate_execution_policy(
            body.get("execution_timeout_seconds", 1800), body.get("max_retries", 0)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    execution = AutomationExecution(
        execution_type="suite",
        target_type="suite",
        target_id=suite.id,
        user_id=current_user.id,
        env_id=body.get("env_id", suite.env_id),
        status="queued",
        idempotency_key=key,
        result_summary={
            "trigger": "manual",
            "execution_timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
        },
    )
    db.add(execution)
    await db.flush()
    db.add_all(
        AutomationExecutionItem(
            execution_id=execution.id,
            sequence=index,
            target_type="scenario",
            target_id=row["scenario_id"],
            target_name=row["name"],
            status="queued",
        )
        for index, row in enumerate(scenario_rows)
    )
    db.add(
        ExecutionEvent(
            execution_id=execution.id,
            sequence=1,
            event_type="execution_queued",
            payload_redacted={"suite_id": suite.id},
        )
    )
    await db.commit()
    await db.refresh(execution)
    await _dispatch_execution(execution)
    return await _execution_payload(db, execution)


@router.post("/executions/{execution_id}/cancel")
@audit_log("cancel", "execution", resource_id_param="execution_id")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(require_permissions("execution:cancel")),
    db: AsyncSession = Depends(get_autotest_db),
):
    execution = await db.scalar(
        select(AutomationExecution).where(
            AutomationExecution.public_id == execution_id,
            AutomationExecution.user_id == current_user.id,
        )
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="执行记录不存在或无权访问")
    if execution.status == "queued":
        execution.status = "cancelled"
        execution.finished_at = _utcnow()
        await db.execute(
            update(AutomationExecutionItem)
            .where(
                AutomationExecutionItem.execution_id == execution.id,
                AutomationExecutionItem.status == "queued",
            )
            .values(status="cancelled", finished_at=execution.finished_at, error_message="执行在开始前被取消")
        )
    elif execution.status == "running":
        execution.status = "cancel_requested"
    elif execution.status not in {"cancelled", "cancel_requested"}:
        raise HTTPException(status_code=409, detail="执行已经结束，不能取消")
    sequence = (
        await db.scalar(
            select(func.coalesce(func.max(ExecutionEvent.sequence), 0)).where(
                ExecutionEvent.execution_id == execution.id
            )
        )
    ) + 1
    db.add(
        ExecutionEvent(
            execution_id=execution.id,
            sequence=sequence,
            level="warning",
            event_type="cancel_requested",
            payload_redacted={},
        )
    )
    await db.commit()
    return await _execution_payload(db, execution)


@router.get("/{suite_id}/runs")
async def list_suite_runs(
    suite_id: int,
    current_user: User = Depends(require_permissions("suite:read")),
    db: AsyncSession = Depends(get_autotest_db),
):
    await _suite_or_404(db, suite_id, current_user.id)
    executions = list(
        (
            await db.scalars(
                select(AutomationExecution)
                .where(
                    AutomationExecution.target_type == "suite",
                    AutomationExecution.target_id == suite_id,
                    AutomationExecution.user_id == current_user.id,
                )
                .order_by(AutomationExecution.created_at.desc())
                .limit(100)
            )
        ).all()
    )
    return {"runs": [await _execution_payload(db, execution) for execution in executions], "total": len(executions)}


@router.get("/{suite_id}/schedule")
async def get_suite_schedule(
    suite_id: int,
    current_user: User = Depends(require_permissions("suite:read")),
    db: AsyncSession = Depends(get_autotest_db),
):
    suite = await _suite_or_404(db, suite_id, current_user.id)
    schedule = await db.scalar(select(TestSuiteSchedule).where(TestSuiteSchedule.suite_id == suite.id))
    return {"schedule": schedule_payload(schedule) if schedule else None}


@router.put("/{suite_id}/schedule")
@audit_log("schedule", "suite", resource_id_param="suite_id")
async def upsert_suite_schedule(
    suite_id: int,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("suite:schedule")),
    db: AsyncSession = Depends(get_autotest_db),
):
    suite = await _suite_or_404(db, suite_id, current_user.id)
    schedule = await db.scalar(select(TestSuiteSchedule).where(TestSuiteSchedule.suite_id == suite.id))
    try:
        cron, timezone_name, misfire_policy, max_concurrent = validate_schedule_config(
            body.get("cron_expression", schedule.cron_expression if schedule else None),
            body.get("timezone_name", schedule.timezone_name if schedule else "Asia/Shanghai"),
            body.get("misfire_policy", schedule.misfire_policy if schedule else "coalesce"),
            body.get("max_concurrent", schedule.max_concurrent if schedule else 1),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        execution_timeout_seconds, max_retries = validate_execution_policy(
            body.get(
                "execution_timeout_seconds",
                schedule.execution_timeout_seconds if schedule else 1800,
            ),
            body.get("max_retries", schedule.max_retries if schedule else 0),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if "notification_config" in body:
        raw_notification_config = body.get("notification_config")
        try:
            if raw_notification_config in (None, {}) or (
                isinstance(raw_notification_config, dict) and raw_notification_config.get("remove") is True
            ):
                notification_config = {}
            else:
                if not isinstance(raw_notification_config, dict):
                    raise ValueError("notification_config must be an object")
                if not str(raw_notification_config.get("webhook_url") or "").strip():
                    if schedule is None or not schedule.notification_config:
                        raise ValueError("请填写通知机器人地址")
                    existing_runtime = notification_config_runtime(schedule.notification_config)
                    raw_notification_config = {
                        **existing_runtime,
                        **raw_notification_config,
                        "webhook_url": existing_runtime["webhook_url"],
                    }
                notification_config = protect_notification_config(validate_notification_config(raw_notification_config))
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    else:
        notification_config = schedule.notification_config if schedule else {}
    if len(json.dumps(notification_config, ensure_ascii=True, default=str)) > 20_000:
        raise HTTPException(status_code=422, detail="notification_config is too large")
    if schedule is None:
        schedule = TestSuiteSchedule(suite_id=suite.id, cron_expression=cron, timezone_name=timezone_name)
        db.add(schedule)
        await db.flush()
    schedule.cron_expression = cron
    schedule.timezone_name = timezone_name
    schedule.misfire_policy = misfire_policy
    schedule.max_concurrent = max_concurrent
    schedule.execution_timeout_seconds = execution_timeout_seconds
    schedule.max_retries = max_retries
    schedule.env_id = body.get("env_id", schedule.env_id if schedule.env_id is not None else suite.env_id)
    is_active = body.get("is_active", schedule.is_active)
    if not isinstance(is_active, bool):
        raise HTTPException(status_code=422, detail="is_active must be a boolean")
    schedule.is_active = is_active
    schedule.notification_config = notification_config
    schedule.updated_at = _utcnow()
    try:
        schedule.next_run_at = install_suite_schedule_job(schedule)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"unable to schedule suite: {exc}") from exc
    await db.commit()
    await db.refresh(schedule)
    return {"schedule": schedule_payload(schedule)}


@router.delete("/{suite_id}/schedule")
async def delete_suite_schedule(
    suite_id: int,
    current_user: User = Depends(require_permissions("suite:schedule")),
    db: AsyncSession = Depends(get_autotest_db),
):
    suite = await _suite_or_404(db, suite_id, current_user.id)
    schedule = await db.scalar(select(TestSuiteSchedule).where(TestSuiteSchedule.suite_id == suite.id))
    if schedule is None:
        return {"deleted": False}
    remove_suite_schedule_job(schedule.id)
    await db.delete(schedule)
    await db.commit()
    return {"deleted": True}


@router.get("/{suite_id}")
async def get_suite(
    suite_id: int,
    current_user: User = Depends(require_permissions("suite:read")),
    db: AsyncSession = Depends(get_autotest_db),
):
    await _migrate_legacy_suites(db, current_user.id)
    return await _suite_payload(db, await _suite_or_404(db, suite_id, current_user.id))


@router.put("/{suite_id}")
async def update_suite(
    suite_id: int,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("suite:update")),
    db: AsyncSession = Depends(get_autotest_db),
):
    suite = await _suite_or_404(db, suite_id, current_user.id)
    if "name" in body:
        name = str(body.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="套件名称不能为空")
        suite.name = name[:200]
    if "description" in body:
        suite.description = str(body.get("description") or "")
    if "env_id" in body:
        suite.env_id = body.get("env_id")
    if "scenario_ids" in body:
        scenario_ids = await _validate_scenarios(db, body.get("scenario_ids") or [], current_user.id)
        await db.execute(delete(TestSuiteScenario).where(TestSuiteScenario.suite_id == suite.id))
        db.add_all(
            TestSuiteScenario(suite_id=suite.id, scenario_id=scenario_id, sort_order=index)
            for index, scenario_id in enumerate(scenario_ids)
        )
    suite.updated_at = _utcnow()
    await db.commit()
    await db.refresh(suite)
    return await _suite_payload(db, suite)


@router.delete("/{suite_id}")
async def delete_suite(
    suite_id: int,
    current_user: User = Depends(require_permissions("suite:delete")),
    db: AsyncSession = Depends(get_autotest_db),
):
    suite = await _suite_or_404(db, suite_id, current_user.id)
    schedule = await db.scalar(select(TestSuiteSchedule).where(TestSuiteSchedule.suite_id == suite.id))
    if schedule is not None:
        remove_suite_schedule_job(schedule.id)
    await db.execute(delete(TestSuiteScenario).where(TestSuiteScenario.suite_id == suite.id))
    await db.execute(delete(TestSuiteSchedule).where(TestSuiteSchedule.suite_id == suite.id))
    await db.execute(delete(TestSuiteCase).where(TestSuiteCase.suite_id == suite.id))
    await db.delete(suite)
    await db.commit()
    return {"message": "测试套件已删除"}
