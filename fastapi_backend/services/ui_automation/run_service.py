"""UI Automation run lifecycle service."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.config import settings
from fastapi_backend.core.exceptions import NotFoundException, ValidationException
from fastapi_backend.models.autotest import ArtifactManifest, AutomationExecution, ExecutionEvent
from fastapi_backend.models.ui_automation import DesktopAgent, UIArtifact, UICaseVersion, UIRun, UIStepResult
from fastapi_backend.services.ui_automation import case_service

TERMINAL_STATUSES = {"passed", "failed", "cancelled", "timed_out", "infra_error"}
ALLOWED_TRANSITIONS = {
    "queued": {"assigned", "waiting_for_agent", "cancelled", "starting", "running", "infra_error"},
    "waiting_for_agent": {"assigned", "cancelled", "infra_error"},
    "assigned": {"starting", "running", "cancel_requested", "cancelled", "infra_error"},
    "starting": {"running", "cancel_requested", "cancelled", "infra_error"},
    "running": {"passed", "failed", "cancel_requested", "cancelled", "timed_out", "infra_error"},
    # The Agent acknowledges this durable directive with ``run:finish``.
    "cancel_requested": {"cancelled", "infra_error"},
}
# The desktop Agent contract is a 30-second lease; heartbeats are emitted more
# frequently so a single delayed browser action does not create a false orphan.
_LEASE_SECONDS = 30
_SENSITIVE_KEY = ("password", "passwd", "secret", "token", "authorization", "cookie", "api_key", "private_key")
_SENSITIVE_KEY_PATTERN = re.compile(
    r"password|passwd|secret|token|api[_-]?key|authorization|cookie|session|id_?card|phone", re.I
)
_SENSITIVE_TEXT_PATTERN = re.compile(
    r"\b(password|passwd|secret|token|api[_-]?key|authorization|cookie|session)\s*([:=])\s*([^\s,;\"'}\]]+)",
    re.I,
)
_URL_PATTERN = re.compile(r"https?://[^\s\"']+", re.I)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _lease_until(now: datetime | None = None) -> datetime:
    return (now or _utcnow()) + timedelta(seconds=_LEASE_SECONDS)


def _duration_ms(started_at: datetime, finished_at: datetime) -> int:
    """Subtract timestamps consistently across SQLite and timezone-aware databases."""
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    else:
        started_at = started_at.astimezone(timezone.utc)
    if finished_at.tzinfo is None:
        finished_at = finished_at.replace(tzinfo=timezone.utc)
    else:
        finished_at = finished_at.astimezone(timezone.utc)
    return max(0, int((finished_at - started_at).total_seconds() * 1000))


def _redact_payload(value: Any, key: str = "") -> Any:
    """Never mirror desktop diagnostics into the authoritative event stream verbatim."""
    if any(term in key.lower() for term in _SENSITIVE_KEY) or _SENSITIVE_KEY_PATTERN.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(name)[:100]: _redact_payload(item, str(name)) for name, item in value.items()}
    if isinstance(value, list):
        return [_redact_payload(item, key) for item in value[:100]]
    if isinstance(value, str):
        return _redact_text(value)[:4096]
    return value


def _redact_url_query(value: str) -> str:
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return value
        pairs = [
            (name, "[REDACTED]" if _SENSITIVE_KEY_PATTERN.search(name) else raw_value)
            for name, raw_value in parse_qsl(parsed.query, keep_blank_values=True)
        ]
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(pairs, doseq=True), ""))
    except (TypeError, ValueError):
        return value


def _redact_text(value: str) -> str:
    """Scrub text/JSON diagnostics too, because browser messages are unstructured."""
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = None
    if isinstance(parsed, (dict, list)):
        return json.dumps(_redact_payload(parsed), ensure_ascii=False, default=str)
    return _URL_PATTERN.sub(
        lambda match: _redact_url_query(match.group(0)), _SENSITIVE_TEXT_PATTERN.sub(r"\1\2[REDACTED]", value)
    )


def _normalize_status(status: str | None) -> str:
    value = (status or "infra_error").strip().lower()
    return {"error": "infra_error", "orphaned": "infra_error"}.get(value, value)


async def _ensure_authoritative_execution(db: AsyncSession, run: UIRun) -> AutomationExecution:
    if run.automation_execution_id:
        execution = await db.get(AutomationExecution, run.automation_execution_id)
        if execution is not None:
            return execution
    execution = AutomationExecution(
        execution_type="ui",
        target_type="ui_run",
        target_id=run.id,
        user_id=run.user_id,
        env_id=run.environment_id,
        status="waiting_for_agent" if run.status == "waiting_for_agent" else "queued",
        attempt=run.attempt,
        idempotency_key=f"ui-run:{run.user_id}:{run.run_key}",
        runner_id=f"desktop-agent:{run.agent_id}" if run.agent_id else "desktop-manual",
        result_summary={"ui_run_id": run.id, "total_steps": run.total_steps},
    )
    db.add(execution)
    await db.flush()
    run.automation_execution_id = execution.id
    db.add(
        ExecutionEvent(
            execution_id=execution.id,
            sequence=1,
            event_type="execution_queued",
            payload_redacted={"ui_run_id": run.id, "trigger_type": run.trigger_type},
        )
    )
    return execution


async def _sync_authoritative_execution(
    db: AsyncSession,
    run: UIRun,
    event: dict[str, Any],
    now: datetime,
) -> None:
    execution = await _ensure_authoritative_execution(db, run)
    event_type = str(event.get("type") or "log")
    status = _normalize_status(run.status)
    execution.status = status
    execution.heartbeat_at = now
    execution.runner_id = f"desktop-agent:{run.agent_id}" if run.agent_id else "desktop-manual"
    execution.result_summary = {
        "ui_run_id": run.id,
        "total_steps": run.total_steps,
        "passed_steps": run.passed_steps,
        "failed_steps": run.failed_steps,
        "skipped_steps": run.skipped_steps,
    }
    if status == "running" and execution.started_at is None:
        execution.started_at = run.started_at or now
    if status in TERMINAL_STATUSES:
        execution.finished_at = run.finished_at or now
        if status in {"timed_out", "infra_error"}:
            execution.error_code = status.upper()
            execution.error_message = str(_redact_payload(event.get("error") or event.get("reason") or status))[:2000]
    next_sequence = (
        int(
            (
                await db.scalar(
                    select(func.coalesce(func.max(ExecutionEvent.sequence), 0)).where(
                        ExecutionEvent.execution_id == execution.id
                    )
                )
            )
            or 0
        )
        + 1
    )
    db.add(
        ExecutionEvent(
            execution_id=execution.id,
            sequence=next_sequence,
            level=str(event.get("level") or ("error" if status in {"failed", "infra_error"} else "info"))[:20],
            event_type=f"ui_{event_type.replace(':', '_')[:72]}",
            payload_redacted=_redact_payload(event),
            created_at=now,
        )
    )


def _build_storage_rel(run: UIRun, artifact_type: str, safe_name: str) -> str:
    return (Path("ui_automation") / "artifacts" / run.run_key / f"{artifact_type}-{safe_name}").as_posix()


def _safe_artifact_filename(value: Any) -> str:
    raw = str(value or "").strip()
    # Normalize both POSIX and Windows separators before validating the final name.
    name = raw.replace("\\", "/").rsplit("/", 1)[-1]
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', "_", name).strip(" .")
    if not name or not any(char.isalnum() for char in name):
        raise ValidationException("Artifact filename is invalid", code="INVALID_ARTIFACT_FILENAME")
    return name[:255]


async def get_run(db: AsyncSession, user_id: int, run_id: int) -> UIRun:
    run = await db.get(UIRun, run_id)
    if not run or run.user_id != user_id:
        raise NotFoundException(f"UI run {run_id} not found")
    return run


async def list_runs(
    db: AsyncSession,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    case_id: Optional[int] = None,
    suite_id: Optional[int] = None,
) -> tuple[list[UIRun], int]:
    query = select(UIRun).where(UIRun.user_id == user_id)
    if status:
        query = query.where(UIRun.status == status)
    if case_id is not None:
        query = query.where(UIRun.case_id == case_id)
    if suite_id is not None:
        query = query.where(UIRun.suite_id == suite_id)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(query.order_by(UIRun.queued_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def create_run(db: AsyncSession, user_id: int, payload: dict[str, Any]) -> UIRun:
    case_id = payload.get("case_id")
    suite_id = payload.get("suite_id")
    client_run_key = payload.get("client_run_key")
    agent_id = payload.get("agent_id")
    trigger_type = payload.get("trigger_type", "manual")
    if bool(case_id) == bool(suite_id):
        raise ValidationException("Exactly one of case_id or suite_id is required")

    if client_run_key:
        existing_q = select(UIRun).where(
            and_(
                UIRun.user_id == user_id,
                UIRun.client_run_key == client_run_key,
            )
        )
        existing = (await db.execute(existing_q)).scalar_one_or_none()
        if existing:
            return existing

    if agent_id is not None:
        agent = await db.get(DesktopAgent, agent_id)
        if agent is None or agent.owner_id != user_id or agent.revoked_at is not None:
            raise ValidationException("Selected desktop Agent is not available", code="AGENT_NOT_AVAILABLE")
        initial_status = "waiting_for_agent"
    elif trigger_type != "manual":
        raise ValidationException("Unattended UI runs require an assigned desktop Agent", code="AGENT_REQUIRED")
    else:
        initial_status = "queued"

    if suite_id is not None:
        from fastapi_backend.services.ui_automation import suite_service

        plan = await suite_service.build_execution_plan(db, user_id, suite_id)
        total_steps = sum(len(entry.get("snapshot", {}).get("steps", [])) for entry in plan["entries"])
        run = UIRun(
            project_id=None,
            case_id=None,
            case_version_id=None,
            suite_id=suite_id,
            agent_id=agent_id,
            client_run_key=client_run_key,
            trigger_type=trigger_type,
            triggered_by=user_id,
            status=initial_status,
            environment_id=payload.get("environment_id"),
            total_steps=total_steps,
            passed_steps=0,
            failed_steps=0,
            skipped_steps=0,
            user_id=user_id,
            artifact_manifest={"artifacts": [], "_last_sequence": 0, "suite_entries": len(plan["entries"])},
        )
        db.add(run)
        await db.flush()
        run.last_heartbeat_at = _utcnow()
        run.lease_expires_at = _lease_until(run.last_heartbeat_at)
        await _ensure_authoritative_execution(db, run)
        return run
    case = await case_service.get_case(db, user_id, case_id)
    version_id = payload.get("case_version_id") or case.current_version_id
    if not version_id:
        raise ValidationException("The case has no saved version to execute")
    version = await case_service.get_version(db, case.id, version_id, user_id)
    snapshot = version.snapshot_json or {}
    steps = snapshot.get("steps", [])

    run = UIRun(
        project_id=case.project_id,
        case_id=case.id,
        case_version_id=version.id,
        suite_id=None,
        agent_id=agent_id,
        client_run_key=client_run_key,
        trigger_type=trigger_type,
        triggered_by=user_id,
        status=initial_status,
        environment_id=payload.get("environment_id"),
        total_steps=len(steps),
        passed_steps=0,
        failed_steps=0,
        skipped_steps=0,
        user_id=user_id,
        artifact_manifest={"artifacts": [], "_last_sequence": 0},
    )
    db.add(run)
    await db.flush()
    run.last_heartbeat_at = _utcnow()
    run.lease_expires_at = _lease_until(run.last_heartbeat_at)
    await _ensure_authoritative_execution(db, run)
    return run


async def list_step_results(db: AsyncSession, user_id: int, run_id: int) -> list[UIStepResult]:
    await get_run(db, user_id, run_id)
    result = await db.execute(select(UIStepResult).where(UIStepResult.run_id == run_id).order_by(UIStepResult.id.asc()))
    return result.scalars().all()


async def list_artifacts(db: AsyncSession, user_id: int, run_id: int) -> list[UIArtifact]:
    await get_run(db, user_id, run_id)
    result = await db.execute(
        select(UIArtifact).where(UIArtifact.run_id == run_id).order_by(UIArtifact.created_at.asc(), UIArtifact.id.asc())
    )
    return result.scalars().all()


async def read_artifact_content(
    db: AsyncSession, user_id: int, run_id: int, artifact_id: int
) -> tuple[UIArtifact, bytes]:
    await get_run(db, user_id, run_id)
    artifact = await db.get(UIArtifact, artifact_id)
    if not artifact or artifact.run_id != run_id:
        raise NotFoundException(f"UI artifact {artifact_id} not found")
    if artifact.artifact_manifest_id:
        raise ValidationException("Use the shared artifact download endpoint", code="USE_SHARED_ARTIFACT_DOWNLOAD")
    root = Path("instance").resolve()
    candidate = (Path("instance") / artifact.storage_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValidationException("Artifact storage path is invalid")
    if not candidate.is_file():
        raise NotFoundException(f"UI artifact content {artifact_id} not found")
    max_bytes = int(getattr(settings, "UI_AUTOMATION_ARTIFACT_MAX_BYTES", 10 * 1024 * 1024) or 10 * 1024 * 1024)
    if candidate.stat().st_size > max_bytes:
        raise ValidationException("Artifact exceeds download size limit", code="ARTIFACT_TOO_LARGE")
    return artifact, candidate.read_bytes()


async def register_artifact(db: AsyncSession, user_id: int, run_id: int, payload: dict[str, Any]) -> UIArtifact:
    run = await get_run(db, user_id, run_id)
    safe_name = _safe_artifact_filename(payload["filename"])
    storage_path = _build_storage_rel(run, payload["type"], safe_name)
    artifact = UIArtifact(
        run_id=run.id,
        type=payload["type"],
        filename=safe_name,
        mime_type=payload.get("mime_type"),
        size_bytes=payload.get("size_bytes"),
        storage_path=storage_path,
        storage_type="local",
    )
    db.add(artifact)
    await db.flush()

    manifest = dict(run.artifact_manifest or {})
    artifacts = list(manifest.get("artifacts", []))
    artifacts.append(
        {"id": artifact.id, "type": artifact.type, "filename": artifact.filename, "storage_path": artifact.storage_path}
    )
    manifest["artifacts"] = artifacts
    run.artifact_manifest = manifest
    await db.flush()
    return artifact


async def link_artifact_manifest(
    db: AsyncSession,
    user_id: int,
    run_id: int,
    artifact_manifest_id: int,
) -> UIArtifact:
    """Attach an already completed shared upload to a UI run without copying bytes."""
    run = await get_run(db, user_id, run_id)
    execution = await _ensure_authoritative_execution(db, run)
    manifest = await db.scalar(
        select(ArtifactManifest).where(
            ArtifactManifest.id == artifact_manifest_id,
            ArtifactManifest.execution_id == execution.id,
        )
    )
    if manifest is None:
        raise ValidationException("Artifact does not belong to this UI run", code="ARTIFACT_OWNERSHIP_MISMATCH")
    existing = await db.scalar(select(UIArtifact).where(UIArtifact.artifact_manifest_id == manifest.id))
    if existing is not None:
        return existing
    artifact = UIArtifact(
        run_id=run.id,
        type=manifest.kind,
        filename=manifest.filename,
        mime_type=manifest.content_type,
        size_bytes=manifest.size_bytes,
        storage_path=f"artifact-manifest:{manifest.id}",
        storage_type="shared",
        artifact_manifest_id=manifest.id,
    )
    db.add(artifact)
    manifest_summary = dict(run.artifact_manifest or {})
    artifacts = list(manifest_summary.get("artifacts") or [])
    artifacts.append(
        {"id": artifact.id, "artifact_manifest_id": manifest.id, "type": artifact.type, "filename": artifact.filename}
    )
    manifest_summary["artifacts"] = artifacts
    run.artifact_manifest = manifest_summary
    await db.flush()
    return artifact


async def upload_artifact_content(db: AsyncSession, user_id: int, run_id: int, payload: dict[str, Any]) -> UIArtifact:
    del db, user_id, run_id, payload
    raise ValidationException(
        "Base64 artifact upload is retired; create a shared upload session and link the completed manifest instead",
        code="USE_RESUMABLE_ARTIFACT_UPLOAD",
    )


async def append_run_events(
    db: AsyncSession, user_id: int, run_id: int, events: list[dict[str, Any]]
) -> tuple[int, int, int, UIRun]:
    run = await db.scalar(select(UIRun).where(UIRun.id == run_id, UIRun.user_id == user_id).with_for_update())
    if run is None:
        raise NotFoundException(f"UI run {run_id} not found")
    manifest = dict(run.artifact_manifest or {})
    last_sequence = int(manifest.get("_last_sequence", 0) or 0)
    accepted = 0
    ignored = 0

    pending: list[dict[str, Any]] = []
    seen_sequences: set[int] = set()
    for event in sorted(events, key=lambda item: item["sequence"]):
        seq = event["sequence"]
        if seq <= last_sequence or seq in seen_sequences:
            ignored += 1
            continue
        seen_sequences.add(seq)
        pending.append(event)

    expected_sequence = last_sequence + 1
    for event in pending:
        if event["sequence"] != expected_sequence:
            raise ValidationException(
                f"Event sequence gap: expected {expected_sequence}, got {event['sequence']}",
                code="EVENT_SEQUENCE_GAP",
            )
        expected_sequence += 1

    finish_positions = [index for index, event in enumerate(pending) if event.get("type") == "run:finish"]
    if len(finish_positions) > 1 or (finish_positions and finish_positions[0] != len(pending) - 1):
        raise ValidationException(
            "run:finish must be the final and only terminal event in a batch",
            code="INVALID_TERMINAL_EVENT_ORDER",
        )

    if run.status in TERMINAL_STATUSES and pending:
        raise ValidationException(
            "A terminal UI run cannot accept new events",
            code="RUN_ALREADY_TERMINAL",
        )

    for event in pending:
        seq = event["sequence"]
        await _apply_event(db, run, event)
        last_sequence = seq
        accepted += 1

    manifest = dict(run.artifact_manifest or {})
    manifest["_last_sequence"] = last_sequence
    run.artifact_manifest = manifest
    now = _utcnow()
    if run.status not in TERMINAL_STATUSES:
        run.last_heartbeat_at = now
        run.lease_expires_at = _lease_until(now)
    else:
        run.lease_expires_at = None
    await db.flush()
    return accepted, ignored, last_sequence, run


async def heartbeat_run(db: AsyncSession, user_id: int, run_id: int) -> UIRun:
    run = await get_run(db, user_id, run_id)
    if run.status in TERMINAL_STATUSES:
        return run
    now = _utcnow()
    run.last_heartbeat_at = now
    run.lease_expires_at = _lease_until(now)
    execution = await _ensure_authoritative_execution(db, run)
    execution.heartbeat_at = now
    await db.flush()
    return run


async def cancel_run(db: AsyncSession, user_id: int, run_id: int) -> UIRun:
    """Cancel unclaimed work immediately or send a durable Agent directive."""
    run = await db.scalar(select(UIRun).where(UIRun.id == run_id, UIRun.user_id == user_id).with_for_update())
    if run is None:
        raise NotFoundException(f"UI run {run_id} not found")
    if run.status in TERMINAL_STATUSES or run.status == "cancel_requested":
        return run
    now = _utcnow()
    if run.status in {"queued", "waiting_for_agent"}:
        await _transition_run(run, "cancelled")
        run.started_at = run.started_at or now
        run.finished_at = now
        run.lease_expires_at = None
        run.error_code = "CANCELLED_BY_USER"
        run.error_summary = "Cancelled before desktop execution started"
        await _sync_authoritative_execution(
            db,
            run,
            {
                "type": "run:finish",
                "status": "cancelled",
                "reason": run.error_summary,
            },
            now,
        )
        return run
    await _transition_run(run, "cancel_requested")
    run.error_code = "CANCEL_REQUESTED"
    run.error_summary = "Cancellation requested by user; awaiting desktop Agent acknowledgement"
    manifest = dict(run.artifact_manifest or {})
    manifest["_cancel_requested_at"] = now.isoformat()
    run.artifact_manifest = manifest
    run.last_heartbeat_at = now
    run.lease_expires_at = _lease_until(now)
    await _sync_authoritative_execution(
        db,
        run,
        {
            "type": "cancel_requested",
            "reason": run.error_summary,
        },
        now,
    )
    await db.flush()
    return run


async def _apply_event(db: AsyncSession, run: UIRun, event: dict[str, Any]) -> None:
    event_type = event["type"]
    now = event.get("occurred_at") or _utcnow()

    if event_type == "run:start":
        # The Agent may have queued its start event just before a user clicks
        # cancel. Accept it for ordering/audit purposes without resurrecting
        # the cancellation request, so its following terminal acknowledgement
        # can still be applied.
        if run.status != "cancel_requested":
            await _transition_run(run, "running")
        if run.started_at is None:
            run.started_at = now
        if event.get("totalSteps") is not None:
            run.total_steps = event["totalSteps"]
        await _sync_authoritative_execution(db, run, event, now)
        return

    if event_type == "run:finish":
        status = _normalize_status(event.get("status"))
        await _transition_run(run, status)
        run.finished_at = now
        run.passed_steps = event.get("passedSteps") or run.passed_steps
        run.failed_steps = event.get("failedSteps") or run.failed_steps
        run.skipped_steps = max(run.total_steps - run.passed_steps - run.failed_steps, 0)
        if run.agent_id:
            agent = await db.get(DesktopAgent, run.agent_id)
            if agent is not None:
                agent.current_runs = max(0, agent.current_runs - 1)
        await _sync_authoritative_execution(db, run, event, now)
        return

    if event_type == "step:start":
        step_result = await _get_or_create_step_result(db, run.id, event["stepId"])
        step_result.status = "pending"
        step_result.started_at = now
        await _sync_authoritative_execution(db, run, event, now)
        return

    if event_type in {"step:pass", "step:fail", "step:skip"}:
        step_result = await _get_or_create_step_result(db, run.id, event["stepId"])
        mapping = {"step:pass": "passed", "step:fail": "failed", "step:skip": "skipped"}
        step_result.status = mapping[event_type]
        step_result.finished_at = now
        step_result.duration_ms = event.get("durationMs")
        if step_result.started_at and step_result.finished_at and step_result.duration_ms is None:
            step_result.duration_ms = _duration_ms(step_result.started_at, step_result.finished_at)
        if event_type == "step:fail":
            step_result.error_message = _redact_payload(event.get("error"), "error")
            run.failed_steps += 1
        elif event_type == "step:pass":
            run.passed_steps += 1
        else:
            run.skipped_steps += 1
        await _sync_authoritative_execution(db, run, event, now)
        return

    if event_type in {"console", "network"}:
        manifest = dict(run.artifact_manifest or {})
        diagnostics = list(manifest.get("diagnostics") or [])
        diagnostics.append(
            {
                "type": event_type,
                "occurred_at": now.isoformat() if hasattr(now, "isoformat") else str(now),
                "level": event.get("level"),
                "text": _redact_payload(event.get("text"), "text"),
                "url": _redact_payload(event.get("url"), "url"),
                "method": event.get("method"),
                "http_status": event.get("httpStatus"),
            }
        )
        manifest["diagnostics"] = diagnostics[-500:]
        run.artifact_manifest = manifest
        if run.status not in TERMINAL_STATUSES and run.status != "cancel_requested":
            await _transition_run(run, "running")
        await _sync_authoritative_execution(db, run, event, now)
        return
    if event_type == "log" and run.status not in TERMINAL_STATUSES and run.status != "cancel_requested":
        await _transition_run(run, "running")
    await _sync_authoritative_execution(db, run, event, now)


async def _get_or_create_step_result(db: AsyncSession, run_id: int, step_id: str) -> UIStepResult:
    result = await db.execute(
        select(UIStepResult).where(UIStepResult.run_id == run_id, UIStepResult.step_id == step_id)
    )
    step_result = result.scalar_one_or_none()
    if step_result:
        return step_result
    step_result = UIStepResult(run_id=run_id, step_id=step_id, iteration=0, attempt=1, status="pending")
    db.add(step_result)
    await db.flush()
    return step_result


async def _transition_run(run: UIRun, target_status: str) -> None:
    target_status = _normalize_status(target_status)
    if target_status not in ALLOWED_TRANSITIONS and target_status not in TERMINAL_STATUSES:
        raise ValidationException(f"Unsupported run status: {target_status}")
    if run.status in TERMINAL_STATUSES:
        return
    if run.status == target_status:
        return
    allowed = ALLOWED_TRANSITIONS.get(run.status, set())
    if target_status not in allowed:
        raise ValidationException(f"Illegal run status transition: {run.status} -> {target_status}")
    if run.status not in {"running", "starting"} and target_status in TERMINAL_STATUSES and run.started_at is None:
        run.started_at = _utcnow()
    run.status = target_status


async def get_case_version_snapshot(db: AsyncSession, run: UIRun) -> Optional[UICaseVersion]:
    if not run.case_version_id:
        return None
    return await db.get(UICaseVersion, run.case_version_id)
