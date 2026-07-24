"""Authenticated desktop Agent leasing for unattended UI runs."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import AsyncSessionLocal
from fastapi_backend.models.autotest import AutomationExecution, ExecutionEvent
from fastapi_backend.models.ui_automation import DesktopAgent, UIRun
from fastapi_backend.services.ui_automation import case_service, run_service, suite_service
from fastapi_backend.services.ui_automation.runtime_environment import resolve_runtime_environment

_logger = logging.getLogger(__name__)
_AGENT_HEARTBEAT_SECONDS = 30
_CANCEL_ACK_TIMEOUT_SECONDS = 60
_WATCHDOG_INTERVAL_SECONDS = 10
_watchdog_task: asyncio.Task | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def _execution_event(
    db: AsyncSession, execution: AutomationExecution, event_type: str, payload: dict[str, Any], level: str = "info"
) -> None:
    sequence = (
        await db.scalar(
            select(func.coalesce(func.max(ExecutionEvent.sequence), 0)).where(
                ExecutionEvent.execution_id == execution.id
            )
        )
    ) or 0
    db.add(
        ExecutionEvent(
            execution_id=execution.id,
            sequence=sequence + 1,
            event_type=event_type,
            level=level,
            payload_redacted=run_service._redact_payload(payload),
        )
    )


async def register_agent(
    db: AsyncSession, user_id: int, payload: dict[str, Any], *, project_id: int | None = None
) -> tuple[DesktopAgent, str]:
    raw_token = secrets.token_urlsafe(32)
    agent = DesktopAgent(
        name=str(payload["name"]).strip(),
        owner_id=user_id,
        project_id=project_id,
        hostname=str(payload.get("hostname") or "")[:200] or None,
        os_version=str(payload.get("os_version") or "")[:100] or None,
        desktop_version=str(payload.get("desktop_version") or "")[:50] or None,
        capabilities=payload.get("capabilities") or {},
        max_parallel=int(payload.get("max_parallel") or 1),
        status="online",
        last_heartbeat_at=_utcnow(),
        agent_token_hash=_token_hash(raw_token),
    )
    db.add(agent)
    await db.flush()
    return agent, raw_token


async def list_agents(db: AsyncSession, user_id: int, *, project_id: int) -> list[DesktopAgent]:
    return list(
        (
            await db.scalars(
                select(DesktopAgent)
                .where(DesktopAgent.owner_id == user_id, DesktopAgent.project_id == project_id)
                .order_by(DesktopAgent.created_at.desc())
            )
        ).all()
    )


async def revoke_agent(db: AsyncSession, user_id: int, agent_id: int, *, project_id: int) -> DesktopAgent:
    """Idempotently revoke an Agent and terminalize work it can no longer run."""
    agent = await db.scalar(
        select(DesktopAgent)
        .where(
            DesktopAgent.id == agent_id,
            DesktopAgent.owner_id == user_id,
            DesktopAgent.project_id == project_id,
        )
        .with_for_update()
    )
    if agent is None:
        raise HTTPException(status_code=404, detail="Desktop Agent was not found")
    if agent.revoked_at is not None:
        return agent

    now = _utcnow()
    runs = list(
        (
            await db.scalars(
                select(UIRun)
                .where(
                    UIRun.agent_id == agent.id,
                    UIRun.user_id == user_id,
                    UIRun.project_id == project_id,
                    UIRun.status.in_(("waiting_for_agent", "assigned", "starting", "running", "cancel_requested")),
                )
                .with_for_update(skip_locked=True)
            )
        ).all()
    )
    for run in runs:
        run.status = "infra_error"
        run.finished_at = now
        run.lease_expires_at = None
        run.error_code = "AGENT_REVOKED"
        run.error_summary = "The assigned Desktop Agent was revoked before execution completed"
        execution = await run_service._ensure_authoritative_execution(db, run)
        execution.status = "infra_error"
        execution.finished_at = now
        execution.heartbeat_at = now
        execution.error_code = run.error_code
        execution.error_message = run.error_summary
        await _execution_event(
            db,
            execution,
            "execution_infrastructure_error",
            {
                "error_code": run.error_code,
                "ui_run_id": run.id,
                "agent_id": agent.id,
            },
            "error",
        )

    agent.revoked_at = now
    agent.status = "revoked"
    agent.current_runs = 0
    return agent


async def authenticate_agent(db: AsyncSession, agent_id: int, token: str | None) -> DesktopAgent:
    agent = await db.get(DesktopAgent, agent_id)
    if agent is None or agent.revoked_at is not None or not token or not agent.agent_token_hash:
        raise HTTPException(status_code=401, detail="Desktop Agent authentication failed")
    if not hmac.compare_digest(agent.agent_token_hash, _token_hash(token)):
        raise HTTPException(status_code=401, detail="Desktop Agent authentication failed")
    return agent


async def heartbeat_agent(db: AsyncSession, agent: DesktopAgent, payload: dict[str, Any] | None = None) -> list[int]:
    now = _utcnow()
    agent.status = "online"
    agent.last_heartbeat_at = now
    if payload and isinstance(payload.get("capabilities"), dict):
        agent.capabilities = payload["capabilities"]
    # Reconcile the counter from durable active run state instead of trusting a client value.
    active_statuses = ("assigned", "starting", "running", "cancel_requested")
    agent.current_runs = int(
        (
            await db.scalar(
                select(func.count())
                .select_from(UIRun)
                .where(
                    UIRun.agent_id == agent.id,
                    UIRun.status.in_(active_statuses),
                )
            )
        )
        or 0
    )
    active_runs = list(
        (await db.scalars(select(UIRun).where(UIRun.agent_id == agent.id, UIRun.status.in_(active_statuses)))).all()
    )
    cancel_run_ids: list[int] = []
    # The Agent heartbeat renews every assigned run lease. Browser navigation,
    # uploads and explicit waits legitimately last longer than one event gap.
    for run in active_runs:
        run.last_heartbeat_at = now
        run.lease_expires_at = run_service._lease_until(now)
        execution = await run_service._ensure_authoritative_execution(db, run)
        execution.heartbeat_at = now
        if run.status == "cancel_requested":
            cancel_run_ids.append(run.id)
    return cancel_run_ids


def _suite_execution_id_for_run(run: UIRun) -> int:
    """Parent suite run id is the shard suite_execution_id; child runs store parent_run_id."""
    manifest = run.artifact_manifest if isinstance(run.artifact_manifest, dict) else {}
    parent = manifest.get("parent_run_id") or manifest.get("suite_execution_id")
    if parent is not None:
        try:
            return int(parent)
        except (TypeError, ValueError):
            pass
    return int(run.id)


async def _filter_suite_plan_for_shard(
    db: AsyncSession,
    agent: DesktopAgent,
    run: UIRun,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """If suite shards exist for this run, claim one and filter plan entries to its case_ids.

    Without shards the full suite plan is returned (single-agent serial path).
    Child fan-out runs resolve suite_execution_id via artifact_manifest.parent_run_id.
    """
    from fastapi_backend.models.feature_upgrades import SuiteShard
    from fastapi_backend.services.suite_sharding_service import suite_sharding_service

    suite_execution_id = _suite_execution_id_for_run(run)
    manifest = run.artifact_manifest if isinstance(run.artifact_manifest, dict) else {}
    preferred_shard_id = manifest.get("shard_id")

    has_shards = await db.scalar(
        select(SuiteShard.id).where(SuiteShard.suite_execution_id == suite_execution_id).limit(1)
    )
    if has_shards is None:
        return plan

    shard = None
    # Child runs created for a specific shard should bind that shard first.
    if preferred_shard_id is not None:
        shard = await db.get(SuiteShard, int(preferred_shard_id))
        if shard is not None and int(shard.suite_execution_id) == suite_execution_id:
            if shard.status == "pending" or (
                shard.assigned_agent_id in (None, agent.id)
                and shard.status in ("pending", "assigned", "running")
            ):
                shard.assigned_agent_id = agent.id
                if shard.status == "pending":
                    shard.status = "assigned"
                    shard.assigned_at = _utcnow()
                await db.flush()
            elif shard.assigned_agent_id not in (None, agent.id) and shard.status in ("assigned", "running"):
                shard = None

    # Prefer a shard already assigned to this agent (reclaim after restart).
    if shard is None:
        shard = await db.scalar(
            select(SuiteShard)
            .where(
                SuiteShard.suite_execution_id == suite_execution_id,
                SuiteShard.assigned_agent_id == agent.id,
                SuiteShard.status.in_(("assigned", "running")),
            )
            .order_by(SuiteShard.shard_index, SuiteShard.id)
            .limit(1)
        )
    if shard is None:
        # Claim next pending shard for this suite execution only.
        result = await db.execute(
            select(SuiteShard)
            .where(
                SuiteShard.suite_execution_id == suite_execution_id,
                SuiteShard.status == "pending",
            )
            .order_by(SuiteShard.shard_index, SuiteShard.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        shard = result.scalar_one_or_none()
        if shard is not None:
            shard.assigned_agent_id = agent.id
            shard.status = "assigned"
            shard.assigned_at = _utcnow()
            await db.flush()

    if shard is None:
        # All shards taken — return empty entries so agent finishes cleanly.
        filtered = dict(plan)
        filtered["entries"] = []
        filtered["shard_id"] = None
        filtered["shard_empty"] = True
        return filtered

    await suite_sharding_service.mark_shard_running(db, shard.id)
    allowed = {int(cid) for cid in (shard.case_ids or []) if cid is not None}
    entries = [entry for entry in (plan.get("entries") or []) if int(entry.get("case_id") or 0) in allowed]
    filtered = dict(plan)
    filtered["entries"] = entries
    filtered["shard_id"] = shard.id
    filtered["shard_index"] = shard.shard_index
    filtered["total_shards"] = shard.total_shards
    filtered["shard_case_ids"] = list(shard.case_ids or [])
    filtered["suite_execution_id"] = suite_execution_id
    return filtered


async def _run_plan(db: AsyncSession, agent: DesktopAgent, run: UIRun) -> dict[str, Any]:
    environment = await resolve_runtime_environment(
        db,
        user_id=agent.owner_id,
        environment_id=run.environment_id,
    )
    if run.case_id:
        version = await case_service.get_version(db, run.case_id, run.case_version_id, agent.owner_id)
        snapshot = await _enrich_snapshot_locators(db, version.snapshot_json or {})
        return {
            "kind": "case",
            "snapshot": snapshot,
            "run_id": run.id,
            "environment": environment,
        }
    if run.suite_id:
        plan = await suite_service.build_execution_plan(db, agent.owner_id, run.suite_id)
        # Enrich each entry snapshot locators from element repository.
        enriched_entries = []
        for entry in plan.get("entries") or []:
            item = dict(entry)
            item["snapshot"] = await _enrich_snapshot_locators(db, entry.get("snapshot") or {})
            enriched_entries.append(item)
        plan = {**plan, "entries": enriched_entries}
        plan = await _filter_suite_plan_for_shard(db, agent, run, plan)
        return {
            "kind": "suite",
            "plan": plan,
            "run_id": run.id,
            "environment": environment,
            "shard_id": plan.get("shard_id"),
        }
    raise HTTPException(status_code=409, detail="UI run target is no longer available")


async def _enrich_snapshot_locators(db: AsyncSession, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Resolve element repository locators as the source of truth when elementId is bound."""
    from fastapi_backend.models.feature_upgrades import UIElement

    steps = list(snapshot.get("steps") or [])
    if not steps:
        return snapshot
    element_ids: list[int] = []
    for step in steps:
        loc = step.get("locator") if isinstance(step, dict) else None
        eid = None
        if isinstance(step, dict):
            eid = step.get("element_id")
        if eid is None and isinstance(loc, dict):
            eid = loc.get("elementId") if loc.get("elementId") is not None else loc.get("element_id")
        if eid is not None:
            try:
                element_ids.append(int(eid))
            except (TypeError, ValueError):
                pass
    elements: dict[int, Any] = {}
    if element_ids:
        rows = list((await db.scalars(select(UIElement).where(UIElement.id.in_(set(element_ids))))).all())
        elements = {int(row.id): row for row in rows}

    new_steps = []
    for step in steps:
        if not isinstance(step, dict):
            new_steps.append(step)
            continue
        item = dict(step)
        loc = dict(item.get("locator") or {}) if isinstance(item.get("locator"), dict) else {}
        eid = item.get("element_id")
        if eid is None:
            eid = loc.get("elementId") if loc.get("elementId") is not None else loc.get("element_id")
        try:
            eid_int = int(eid) if eid is not None else None
        except (TypeError, ValueError):
            eid_int = None
        if eid_int is not None and eid_int in elements:
            element = elements[eid_int]
            primary = None
            for candidate in element.locators or []:
                if isinstance(candidate, dict) and candidate.get("strategy") and candidate.get("value") is not None:
                    primary = candidate
                    break
            if primary:
                # Repo locator is source of truth; keep original as first fallback.
                original = loc if loc.get("strategy") and loc.get("value") is not None else None
                fallbacks = list(primary.get("fallbacks") or [])
                if original and (
                    original.get("strategy") != primary.get("strategy")
                    or str(original.get("value")) != str(primary.get("value"))
                ):
                    fallbacks = [original, *fallbacks]
                loc = {
                    **primary,
                    "fallbacks": fallbacks,
                    "elementId": eid_int,
                    "framePath": primary.get("framePath")
                    or primary.get("frame_path")
                    or element.frame_path
                    or loc.get("framePath")
                    or [],
                }
            else:
                loc = {**loc, "elementId": eid_int}
            item["element_id"] = eid_int
            item["locator"] = loc
        elif eid_int is not None and loc:
            loc = {**loc, "elementId": eid_int}
            item["locator"] = loc
            item["element_id"] = eid_int
        new_steps.append(item)
    return {**snapshot, "steps": new_steps}


async def claim_next_run(db: AsyncSession, agent: DesktopAgent) -> tuple[UIRun | None, dict[str, Any] | None]:
    items = await claim_runs(db, agent, limit=1)
    if not items:
        return None, None
    return items[0]


async def claim_runs(
    db: AsyncSession,
    agent: DesktopAgent,
    *,
    limit: int = 1,
) -> list[tuple[UIRun, dict[str, Any]]]:
    """Claim up to `limit` waiting runs while respecting agent.max_parallel."""
    await heartbeat_agent(db, agent)
    available = max(0, int(agent.max_parallel or 1) - int(agent.current_runs or 0))
    take = max(0, min(int(limit or 1), available, 16))
    if take <= 0:
        return []

    result = await db.execute(
        select(UIRun)
        .where(
            UIRun.agent_id == agent.id,
            UIRun.user_id == agent.owner_id,
            UIRun.project_id == agent.project_id,
            UIRun.status == "waiting_for_agent",
        )
        .order_by(UIRun.queued_at, UIRun.id)
        .with_for_update(skip_locked=True)
        .limit(take)
    )
    runs = list(result.scalars().all())
    if not runs:
        return []

    now = _utcnow()
    claimed: list[tuple[UIRun, dict[str, Any]]] = []
    for run in runs:
        run.status = "assigned"
        run.last_heartbeat_at = now
        run.lease_expires_at = run_service._lease_until(now)
        execution = await run_service._ensure_authoritative_execution(db, run)
        execution.status = "assigned"
        execution.runner_id = f"desktop-agent:{agent.id}"
        execution.heartbeat_at = now
        await _execution_event(db, execution, "agent_assigned", {"agent_id": agent.id, "ui_run_id": run.id})
        agent.current_runs = int(agent.current_runs or 0) + 1
        claimed.append((run, await _run_plan(db, agent, run)))
    return claimed


def _is_expired(value: datetime | None, now: datetime | None = None) -> bool:
    if value is None:
        return True
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value < (now or _utcnow())


async def get_agent_run(
    db: AsyncSession,
    agent: DesktopAgent,
    run_id: int,
    *,
    require_active_lease: bool,
    lock: bool = False,
) -> UIRun:
    """Resolve only a run assigned to this exact owner-bound Agent token."""
    query = select(UIRun).where(
        UIRun.id == run_id,
        UIRun.agent_id == agent.id,
        UIRun.user_id == agent.owner_id,
        UIRun.project_id == agent.project_id,
    )
    if lock:
        query = query.with_for_update()
    run = await db.scalar(query)
    if run is None:
        raise HTTPException(status_code=404, detail="Assigned UI run was not found")
    if require_active_lease:
        if run.status not in {"assigned", "starting", "running", "cancel_requested"}:
            raise HTTPException(status_code=409, detail="Assigned UI run is not active")
        if _is_expired(run.lease_expires_at):
            raise HTTPException(status_code=409, detail="Assigned UI run lease has expired")
    return run


async def reconcile_stale_ui_runs(session_factory=None) -> int:
    """Turn abandoned client or Agent leases into terminal infrastructure errors."""
    now = _utcnow()
    factory = session_factory or AsyncSessionLocal
    async with factory() as db:
        stale = list(
            (
                await db.scalars(
                    select(UIRun)
                    .where(
                        UIRun.status.in_(("assigned", "starting", "running")),
                        UIRun.lease_expires_at.is_not(None),
                        UIRun.lease_expires_at < now,
                    )
                    .with_for_update(skip_locked=True)
                )
            ).all()
        )
        for run in stale:
            run.status = "infra_error"
            run.finished_at = now
            run.error_code = "RUNNER_HEARTBEAT_EXPIRED"
            run.error_summary = "Desktop Agent or local desktop runner heartbeat expired"
            execution = await run_service._ensure_authoritative_execution(db, run)
            execution.status = "infra_error"
            execution.finished_at = now
            execution.heartbeat_at = now
            execution.error_code = "RUNNER_HEARTBEAT_EXPIRED"
            execution.error_message = run.error_summary
            await _execution_event(
                db,
                execution,
                "execution_infrastructure_error",
                {
                    "error_code": execution.error_code,
                    "ui_run_id": run.id,
                },
                "error",
            )
            if run.agent_id:
                agent = await db.get(DesktopAgent, run.agent_id)
                if agent:
                    agent.current_runs = max(0, agent.current_runs - 1)
        cancel_requested = list(
            (
                await db.scalars(
                    select(UIRun).where(UIRun.status == "cancel_requested").with_for_update(skip_locked=True)
                )
            ).all()
        )
        cancelled_count = 0
        for run in cancel_requested:
            raw_requested_at = (run.artifact_manifest or {}).get("_cancel_requested_at")
            try:
                requested_at = datetime.fromisoformat(str(raw_requested_at).replace("Z", "+00:00"))
                if requested_at.tzinfo is None:
                    requested_at = requested_at.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                requested_at = now - timedelta(seconds=_CANCEL_ACK_TIMEOUT_SECONDS + 1)
            if requested_at > now - timedelta(seconds=_CANCEL_ACK_TIMEOUT_SECONDS):
                continue
            run.status = "cancelled"
            run.finished_at = now
            run.lease_expires_at = None
            run.error_code = "CANCEL_ACK_TIMEOUT"
            run.error_summary = "Cancellation completed after the Desktop Agent did not acknowledge in time"
            execution = await run_service._ensure_authoritative_execution(db, run)
            execution.status = "cancelled"
            execution.finished_at = now
            execution.heartbeat_at = now
            execution.error_code = run.error_code
            execution.error_message = run.error_summary
            await _execution_event(
                db,
                execution,
                "execution_cancelled",
                {
                    "error_code": run.error_code,
                    "ui_run_id": run.id,
                },
                "warning",
            )
            if run.agent_id:
                agent = await db.get(DesktopAgent, run.agent_id)
                if agent:
                    agent.current_runs = max(0, agent.current_runs - 1)
            cancelled_count += 1
        offline_before = now - timedelta(seconds=_AGENT_HEARTBEAT_SECONDS)
        offline = list(
            (
                await db.scalars(
                    select(DesktopAgent).where(
                        DesktopAgent.status == "online",
                        DesktopAgent.last_heartbeat_at.is_not(None),
                        DesktopAgent.last_heartbeat_at < offline_before,
                    )
                )
            ).all()
        )
        for agent in offline:
            agent.status = "offline"
        await db.commit()
        return len(stale) + cancelled_count


async def _watchdog_loop() -> None:
    while True:
        try:
            await asyncio.sleep(_WATCHDOG_INTERVAL_SECONDS)
            await reconcile_stale_ui_runs()
        except asyncio.CancelledError:
            raise
        except Exception:
            _logger.exception("UI execution watchdog iteration failed; retrying")


async def start_ui_execution_watchdog() -> None:
    global _watchdog_task
    try:
        await reconcile_stale_ui_runs()
    except Exception:
        _logger.exception("Initial UI execution reconciliation failed; watchdog will retry")
    if _watchdog_task is None or _watchdog_task.done():
        _watchdog_task = asyncio.create_task(_watchdog_loop(), name="ui-execution-watchdog")


async def stop_ui_execution_watchdog() -> None:
    global _watchdog_task
    if _watchdog_task is None:
        return
    _watchdog_task.cancel()
    try:
        await _watchdog_task
    except asyncio.CancelledError:
        pass
    _watchdog_task = None
