"""UI Automation run lifecycle service."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.config import settings
from fastapi_backend.core.exceptions import NotFoundException, ValidationException
from fastapi_backend.models.ui_automation import UIArtifact, UICaseVersion, UIRun, UIStepResult
from fastapi_backend.services.ui_automation import case_service

TERMINAL_STATUSES = {'passed', 'failed', 'cancelled', 'error'}
ALLOWED_TRANSITIONS = {
    'queued': {'assigned', 'cancelled', 'starting', 'running'},
    'assigned': {'starting', 'running', 'cancelled', 'orphaned'},
    'starting': {'running', 'cancelled', 'orphaned', 'error'},
    'running': {'passed', 'failed', 'cancelled', 'error'},
    'orphaned': {'queued', 'error'},
}

ARTIFACT_STORAGE_ROOT = Path('instance') / 'ui_automation' / 'artifacts'


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_storage_rel(run: UIRun, artifact_type: str, safe_name: str) -> str:
    return (Path('ui_automation') / 'artifacts' / run.run_key / f'{artifact_type}-{safe_name}').as_posix()


async def get_run(db: AsyncSession, user_id: int, run_id: int) -> UIRun:
    run = await db.get(UIRun, run_id)
    if not run or run.user_id != user_id:
        raise NotFoundException(f'UI run {run_id} not found')
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
    case_id = payload.get('case_id')
    suite_id = payload.get('suite_id')
    client_run_key = payload.get('client_run_key')
    if bool(case_id) == bool(suite_id):
        raise ValidationException('Exactly one of case_id or suite_id is required')

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

    if suite_id is not None:
        from fastapi_backend.services.ui_automation import suite_service
        plan = await suite_service.build_execution_plan(db, user_id, suite_id)
        total_steps = sum(len(entry.get('snapshot', {}).get('steps', [])) for entry in plan['entries'])
        run = UIRun(
            project_id=None, case_id=None, case_version_id=None, suite_id=suite_id,
            agent_id=payload.get('agent_id'), client_run_key=client_run_key,
            trigger_type=payload.get('trigger_type', 'manual'), triggered_by=user_id,
            status='queued', environment_id=payload.get('environment_id'), total_steps=total_steps,
            passed_steps=0, failed_steps=0, skipped_steps=0, user_id=user_id,
            artifact_manifest={'artifacts': [], '_last_sequence': 0, 'suite_entries': len(plan['entries'])},
        )
        db.add(run)
        await db.flush()
        return run
    case = await case_service.get_case(db, user_id, case_id)
    version_id = payload.get('case_version_id') or case.current_version_id
    if not version_id:
        raise ValidationException('The case has no saved version to execute')
    version = await case_service.get_version(db, case.id, version_id, user_id)
    snapshot = version.snapshot_json or {}
    steps = snapshot.get('steps', [])

    run = UIRun(
        project_id=case.project_id,
        case_id=case.id,
        case_version_id=version.id,
        suite_id=None,
        agent_id=payload.get('agent_id'),
        client_run_key=client_run_key,
        trigger_type=payload.get('trigger_type', 'manual'),
        triggered_by=user_id,
        status='queued',
        environment_id=payload.get('environment_id'),
        total_steps=len(steps),
        passed_steps=0,
        failed_steps=0,
        skipped_steps=0,
        user_id=user_id,
        artifact_manifest={'artifacts': [], '_last_sequence': 0},
    )
    db.add(run)
    await db.flush()
    return run


async def list_step_results(db: AsyncSession, user_id: int, run_id: int) -> list[UIStepResult]:
    await get_run(db, user_id, run_id)
    result = await db.execute(select(UIStepResult).where(UIStepResult.run_id == run_id).order_by(UIStepResult.id.asc()))
    return result.scalars().all()


async def list_artifacts(db: AsyncSession, user_id: int, run_id: int) -> list[UIArtifact]:
    await get_run(db, user_id, run_id)
    result = await db.execute(select(UIArtifact).where(UIArtifact.run_id == run_id).order_by(UIArtifact.created_at.asc(), UIArtifact.id.asc()))
    return result.scalars().all()


async def read_artifact_content(db: AsyncSession, user_id: int, run_id: int, artifact_id: int) -> tuple[UIArtifact, bytes]:
    await get_run(db, user_id, run_id)
    artifact = await db.get(UIArtifact, artifact_id)
    if not artifact or artifact.run_id != run_id:
        raise NotFoundException(f'UI artifact {artifact_id} not found')
    root = Path('instance').resolve()
    candidate = (Path('instance') / artifact.storage_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValidationException('Artifact storage path is invalid')
    if not candidate.is_file():
        raise NotFoundException(f'UI artifact content {artifact_id} not found')
    max_bytes = int(getattr(settings, 'UI_AUTOMATION_ARTIFACT_MAX_BYTES', 10 * 1024 * 1024) or 10 * 1024 * 1024)
    if candidate.stat().st_size > max_bytes:
        raise ValidationException('Artifact exceeds download size limit', code='ARTIFACT_TOO_LARGE')
    return artifact, candidate.read_bytes()

async def register_artifact(db: AsyncSession, user_id: int, run_id: int, payload: dict[str, Any]) -> UIArtifact:
    run = await get_run(db, user_id, run_id)
    safe_name = Path(payload['filename']).name
    storage_path = _build_storage_rel(run, payload['type'], safe_name)
    artifact = UIArtifact(
        run_id=run.id,
        type=payload['type'],
        filename=safe_name,
        mime_type=payload.get('mime_type'),
        size_bytes=payload.get('size_bytes'),
        storage_path=storage_path,
        storage_type='local',
    )
    db.add(artifact)
    await db.flush()

    manifest = dict(run.artifact_manifest or {})
    artifacts = list(manifest.get('artifacts', []))
    artifacts.append({'id': artifact.id, 'type': artifact.type, 'filename': artifact.filename, 'storage_path': artifact.storage_path})
    manifest['artifacts'] = artifacts
    run.artifact_manifest = manifest
    await db.flush()
    return artifact


async def upload_artifact_content(db: AsyncSession, user_id: int, run_id: int, payload: dict[str, Any]) -> UIArtifact:
    run = await get_run(db, user_id, run_id)
    artifact_type = payload['type']
    if artifact_type not in {'screenshot', 'video', 'trace', 'console_log', 'network', 'download', 'html_report'}:
        raise ValidationException('Unsupported artifact type')

    safe_name = Path(payload['filename']).name
    if not safe_name:
        raise ValidationException('Artifact filename is required')

    try:
        content = base64.b64decode(payload['content_base64'], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValidationException('Invalid artifact base64 content') from exc

    if not content:
        raise ValidationException('Artifact content cannot be empty')

    max_bytes = int(getattr(settings, 'UI_AUTOMATION_ARTIFACT_MAX_BYTES', 10 * 1024 * 1024) or 10 * 1024 * 1024)
    if len(content) > max_bytes:
        raise ValidationException(f'Artifact exceeds max size limit ({max_bytes} bytes)', code='ARTIFACT_TOO_LARGE')

    storage_rel = _build_storage_rel(run, artifact_type, safe_name)
    storage_path = Path('instance') / storage_rel
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(content)

    artifact = await register_artifact(
        db,
        user_id,
        run_id,
        {
            'type': artifact_type,
            'filename': safe_name,
            'mime_type': payload.get('mime_type'),
            'size_bytes': payload.get('size_bytes') or len(content),
        },
    )
    artifact.storage_path = storage_rel
    artifact.size_bytes = payload.get('size_bytes') or len(content)
    await db.flush()
    return artifact


async def append_run_events(db: AsyncSession, user_id: int, run_id: int, events: list[dict[str, Any]]) -> tuple[int, int, int, UIRun]:
    run = await get_run(db, user_id, run_id)
    manifest = dict(run.artifact_manifest or {})
    last_sequence = int(manifest.get('_last_sequence', 0) or 0)
    accepted = 0
    ignored = 0

    for event in sorted(events, key=lambda item: item['sequence']):
        seq = event['sequence']
        if seq <= last_sequence:
            ignored += 1
            continue
        await _apply_event(db, run, event)
        last_sequence = seq
        accepted += 1

    manifest = dict(run.artifact_manifest or {})
    manifest['_last_sequence'] = last_sequence
    run.artifact_manifest = manifest
    await db.flush()
    return accepted, ignored, last_sequence, run


async def _apply_event(db: AsyncSession, run: UIRun, event: dict[str, Any]) -> None:
    event_type = event['type']
    now = event.get('occurred_at') or _utcnow()

    if event_type == 'run:start':
        await _transition_run(run, 'running')
        if run.started_at is None:
            run.started_at = now
        if event.get('totalSteps') is not None:
            run.total_steps = event['totalSteps']
        return

    if event_type == 'run:finish':
        status = event.get('status') or 'error'
        await _transition_run(run, status)
        run.finished_at = now
        run.passed_steps = event.get('passedSteps') or run.passed_steps
        run.failed_steps = event.get('failedSteps') or run.failed_steps
        run.skipped_steps = max(run.total_steps - run.passed_steps - run.failed_steps, 0)
        return

    if event_type == 'step:start':
        step_result = await _get_or_create_step_result(db, run.id, event['stepId'])
        step_result.status = 'pending'
        step_result.started_at = now
        return

    if event_type in {'step:pass', 'step:fail', 'step:skip'}:
        step_result = await _get_or_create_step_result(db, run.id, event['stepId'])
        mapping = {'step:pass': 'passed', 'step:fail': 'failed', 'step:skip': 'skipped'}
        step_result.status = mapping[event_type]
        step_result.finished_at = now
        step_result.duration_ms = event.get('durationMs')
        if step_result.started_at and step_result.finished_at and step_result.duration_ms is None:
            step_result.duration_ms = int((step_result.finished_at - step_result.started_at).total_seconds() * 1000)
        if event_type == 'step:fail':
            step_result.error_message = event.get('error')
            run.failed_steps += 1
        elif event_type == 'step:pass':
            run.passed_steps += 1
        else:
            run.skipped_steps += 1
        return

    if event_type in {'console', 'network'}:
        manifest = dict(run.artifact_manifest or {})
        diagnostics = list(manifest.get('diagnostics') or [])
        diagnostics.append(
            {
                'type': event_type,
                'occurred_at': now.isoformat() if hasattr(now, 'isoformat') else str(now),
                'level': event.get('level'),
                'text': event.get('text'),
                'url': event.get('url'),
                'method': event.get('method'),
                'http_status': event.get('httpStatus'),
            }
        )
        manifest['diagnostics'] = diagnostics[-500:]
        run.artifact_manifest = manifest
        if run.status not in TERMINAL_STATUSES:
            await _transition_run(run, 'running')
        return
    if event_type == 'log' and run.status not in TERMINAL_STATUSES:
        await _transition_run(run, 'running')


async def _get_or_create_step_result(db: AsyncSession, run_id: int, step_id: str) -> UIStepResult:
    result = await db.execute(select(UIStepResult).where(UIStepResult.run_id == run_id, UIStepResult.step_id == step_id))
    step_result = result.scalar_one_or_none()
    if step_result:
        return step_result
    step_result = UIStepResult(run_id=run_id, step_id=step_id, iteration=0, attempt=1, status='pending')
    db.add(step_result)
    await db.flush()
    return step_result


async def _transition_run(run: UIRun, target_status: str) -> None:
    if target_status not in ALLOWED_TRANSITIONS and target_status not in TERMINAL_STATUSES:
        raise ValidationException(f'Unsupported run status: {target_status}')
    if run.status in TERMINAL_STATUSES:
        return
    if run.status == target_status:
        return
    allowed = ALLOWED_TRANSITIONS.get(run.status, set())
    if target_status not in allowed and target_status not in TERMINAL_STATUSES:
        raise ValidationException(f'Illegal run status transition: {run.status} -> {target_status}')
    if run.status not in {'running', 'starting'} and target_status in TERMINAL_STATUSES and run.started_at is None:
        run.started_at = _utcnow()
    run.status = target_status


async def get_case_version_snapshot(db: AsyncSession, run: UIRun) -> Optional[UICaseVersion]:
    if not run.case_version_id:
        return None
    return await db.get(UICaseVersion, run.case_version_id)








