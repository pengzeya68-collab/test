"""Preview-first, auditable API asset import centre."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup, ImportJob
from fastapi_backend.models.models import User
from fastapi_backend.services.unified_import import (
    ImportSourceError,
    candidate_from_case,
    parse_import,
)


router = APIRouter(prefix="/api/auto-test/import", tags=["Import Center"])
_CONFLICT_STRATEGIES = {"skip", "copy", "update"}
_MAX_IMPORT_BYTES = 20 * 1024 * 1024
_IMPORT_PARSE_TIMEOUT_SECONDS = 15


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _read_upload_bounded(file: UploadFile) -> bytes:
    """Reject oversized uploads while streaming, before buffering the full body."""
    if file.size is not None and file.size > _MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail=f"导入文件不能超过 {_MAX_IMPORT_BYTES // (1024 * 1024)} MB")
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(min(1024 * 1024, _MAX_IMPORT_BYTES + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        if total > _MAX_IMPORT_BYTES:
            raise HTTPException(status_code=413, detail=f"导入文件不能超过 {_MAX_IMPORT_BYTES // (1024 * 1024)} MB")
        chunks.append(chunk)
    return b"".join(chunks)


def _source_summary(
    content: bytes, source_type: str, filename: str, candidate_count: int | None = None
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "source_type": source_type,
        "source_filename": str(filename or "").replace("\\", "/").split("/")[-1][:200],
        "source_size_bytes": len(content),
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "sensitive_values_redacted": True,
    }
    if candidate_count is not None:
        summary["candidate_count"] = candidate_count
    return summary


async def _record_parse_failure(
    db: AsyncSession,
    user_id: int,
    content: bytes,
    source_type: str,
    filename: str,
    error: Exception,
) -> None:
    db.add(
        ImportJob(
            user_id=user_id,
            source_type=source_type[:30] or "unknown",
            status="failed",
            summary=_source_summary(content, source_type or "unknown", filename),
            error_summary=str(error)[:1000],
            completed_at=_utcnow(),
        )
    )
    await db.commit()


def _parse_selected_ids(raw: Optional[str], candidates: list[dict[str, Any]]) -> set[str]:
    known = {candidate["id"] for candidate in candidates}
    if raw is None or not str(raw).strip():
        return known
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="selected_ids 必须是 JSON 数组") from exc
    if not isinstance(values, list) or not values:
        raise HTTPException(status_code=422, detail="selected_ids 必须包含至少一个候选项")
    selected = {str(value) for value in values}
    if len(selected) != len(values) or not selected.issubset(known):
        raise HTTPException(status_code=422, detail="selected_ids 包含无效或重复候选项")
    return selected


async def _ensure_target_group(db: AsyncSession, user_id: int, target_group_id: Optional[int]) -> None:
    if target_group_id is None:
        return
    group = await db.scalar(
        select(AutoTestGroup).where(
            AutoTestGroup.id == target_group_id,
            AutoTestGroup.user_id == user_id,
        )
    )
    if group is None:
        raise HTTPException(status_code=404, detail="目标分组不存在或无权访问")


async def _annotate_conflicts(db: AsyncSession, user_id: int, candidates: list[dict[str, Any]]) -> None:
    """Add exact structural conflicts without treating names as an identity."""
    methods = {candidate["method"] for candidate in candidates}
    urls = {candidate["url"] for candidate in candidates}
    if not methods or not urls:
        return
    existing_cases = list(
        (
            await db.scalars(
                select(AutoTestCase).where(
                    AutoTestCase.user_id == user_id,
                    AutoTestCase.method.in_(methods),
                    AutoTestCase.url.in_(urls),
                )
            )
        ).all()
    )
    by_fingerprint: dict[str, list[AutoTestCase]] = {}
    for case in existing_cases:
        fingerprint = candidate_from_case(case)["fingerprint"]
        by_fingerprint.setdefault(fingerprint, []).append(case)
    for candidate in candidates:
        matches = by_fingerprint.get(candidate["fingerprint"], [])
        candidate["conflicts"] = [{"case_id": case.id, "name": case.name} for case in matches]
        candidate["conflict_count"] = len(matches)


def _case_fields(candidate: dict[str, Any], *, target_group_id: Optional[int], description: str) -> dict[str, Any]:
    return {
        "group_id": target_group_id,
        "name": candidate["name"],
        "method": candidate["method"],
        "url": candidate["url"],
        "headers": candidate["headers"] or None,
        "params": candidate["params"] or None,
        "body_type": candidate["body_type"],
        "content_type": candidate["content_type"],
        "payload": candidate["payload"],
        "assert_rules": candidate["assert_rules"] or None,
        "request_config": (
            {"import_source": candidate.get("source_metadata")} if candidate.get("source_metadata") else None
        ),
        "description": description,
    }


async def _commit_candidates(
    db: AsyncSession,
    *,
    current_user: User,
    source_type: str,
    filename: str,
    content: bytes,
    candidates: list[dict[str, Any]],
    selected_ids: set[str],
    conflict_strategy: str,
    target_group_id: Optional[int],
) -> dict[str, Any]:
    if conflict_strategy not in _CONFLICT_STRATEGIES:
        raise HTTPException(status_code=422, detail="冲突策略仅支持 skip、copy 或 update")
    await _ensure_target_group(db, current_user.id, target_group_id)
    await _annotate_conflicts(db, current_user.id, candidates)
    selected_candidates = [candidate for candidate in candidates if candidate["id"] in selected_ids]
    job = ImportJob(
        user_id=current_user.id,
        source_type=source_type,
        status="running",
        summary={
            **_source_summary(content, source_type, filename, len(candidates)),
            "selected_count": len(selected_candidates),
            "conflict_strategy": conflict_strategy,
        },
    )
    db.add(job)
    # Persist the audit record before the import transaction. If that transaction rolls
    # back, the job is still available with a terminal failure explanation.
    await db.commit()
    await db.refresh(job)

    imported = copied = updated = skipped = 0
    case_ids: list[int] = []
    try:
        for candidate in selected_candidates:
            conflicts = candidate.get("conflicts") or []
            exact_case_id = conflicts[0]["case_id"] if conflicts else None
            description = f"由 {source_type} 导入；凭据已自动脱敏。"
            if exact_case_id is not None and conflict_strategy == "skip":
                skipped += 1
                continue
            if exact_case_id is not None and conflict_strategy == "update":
                existing = await db.scalar(
                    select(AutoTestCase).where(
                        AutoTestCase.id == exact_case_id,
                        AutoTestCase.user_id == current_user.id,
                    )
                )
                if existing is None:
                    raise RuntimeError("冲突用例在导入确认时已被删除")
                fields = _case_fields(candidate, target_group_id=target_group_id, description=description)
                if target_group_id is None:
                    fields.pop("group_id")
                for field, value in fields.items():
                    setattr(existing, field, value)
                case_ids.append(existing.id)
                updated += 1
                continue
            fields = _case_fields(candidate, target_group_id=target_group_id, description=description)
            if exact_case_id is not None:
                fields["name"] = f"{candidate['name']}（导入副本）"[:200]
                copied += 1
            case = AutoTestCase(user_id=current_user.id, **fields)
            db.add(case)
            await db.flush()
            case_ids.append(case.id)
            imported += 1
        job.status = "completed"
        job.completed_at = _utcnow()
        job.summary = {
            **(job.summary or {}),
            "imported_count": imported,
            "copied_count": copied,
            "updated_count": updated,
            "skipped_count": skipped,
            "case_ids": case_ids,
        }
        await db.commit()
    except Exception as exc:
        await db.rollback()
        failed_job = await db.get(ImportJob, job.id)
        if failed_job is not None:
            failed_job.status = "failed"
            failed_job.completed_at = _utcnow()
            failed_job.error_summary = str(exc)[:1000]
            failed_job.summary = {**(failed_job.summary or {}), "imported_count": 0, "failure_stage": "commit"}
            await db.commit()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=409, detail="导入未完成，已回滚所有用例修改") from exc
    return {"import_job_id": job.id, **(job.summary or {})}


async def _parse_or_error(
    db: AsyncSession, current_user: User, content: bytes, source_type: str, filename: str
) -> tuple[str, list[dict[str, Any]]]:
    try:
        parsed_source_type, candidates = await asyncio.wait_for(
            asyncio.to_thread(parse_import, content, source_hint=source_type, filename=filename),
            timeout=_IMPORT_PARSE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        await _record_parse_failure(db, current_user.id, content, source_type or "auto", filename, exc)
        raise HTTPException(status_code=408, detail="导入文件解析超时") from exc
    except ImportSourceError as exc:
        await _record_parse_failure(db, current_user.id, content, source_type or "auto", filename, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _annotate_conflicts(db, current_user.id, candidates)
    return parsed_source_type, candidates


@router.post("/preview")
@audit_log("preview", "api_import")
async def preview_import(
    file: UploadFile = File(...),
    source_type: str = Form("auto"),
    current_user: User = Depends(require_permissions("case:import", "case:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    content = await _read_upload_bounded(file)
    parsed_source_type, candidates = await _parse_or_error(db, current_user, content, source_type, file.filename or "")
    job = ImportJob(
        user_id=current_user.id,
        source_type=parsed_source_type,
        status="previewed",
        summary=_source_summary(content, parsed_source_type, file.filename or "", len(candidates)),
        completed_at=_utcnow(),
    )
    db.add(job)
    await db.commit()
    return {
        "import_job_id": job.id,
        "source_type": parsed_source_type,
        "candidates": candidates,
        "total": len(candidates),
        "sensitive_values_redacted": True,
    }


@router.post("/commit")
@audit_log("import", "api_import")
async def commit_import(
    file: UploadFile = File(...),
    source_type: str = Form("auto"),
    selected_ids: Optional[str] = Form(None),
    conflict_strategy: str = Form("skip"),
    target_group_id: Optional[int] = Form(None),
    current_user: User = Depends(require_permissions("case:import", "case:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    content = await _read_upload_bounded(file)
    parsed_source_type, candidates = await _parse_or_error(db, current_user, content, source_type, file.filename or "")
    selected = _parse_selected_ids(selected_ids, candidates)
    return await _commit_candidates(
        db,
        current_user=current_user,
        source_type=parsed_source_type,
        filename=file.filename or "",
        content=content,
        candidates=candidates,
        selected_ids=selected,
        conflict_strategy=conflict_strategy.lower().strip(),
        target_group_id=target_group_id,
    )


@router.get("/jobs")
async def list_import_jobs(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permissions("case:import")),
    db: AsyncSession = Depends(get_autotest_db),
):
    jobs = list(
        (
            await db.scalars(
                select(ImportJob)
                .where(
                    ImportJob.user_id == current_user.id,
                )
                .order_by(ImportJob.created_at.desc())
                .limit(limit)
            )
        ).all()
    )
    return {
        "items": [
            {
                "id": job.id,
                "source_type": job.source_type,
                "status": job.status,
                "summary": job.summary or {},
                "error_summary": job.error_summary,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
            }
            for job in jobs
        ]
    }


@router.post("/har")
@audit_log("import", "har_import")
async def import_har(
    file: UploadFile = File(...),
    dry_run: bool = Form(True),
    selected_ids: Optional[str] = Form(None),
    conflict_strategy: str = Form("skip"),
    target_group_id: Optional[int] = Form(None),
    current_user: User = Depends(require_permissions("case:import", "case:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """Compatibility endpoint. New callers should use /preview then /commit."""
    content = await _read_upload_bounded(file)
    parsed_source_type, candidates = await _parse_or_error(db, current_user, content, "har", file.filename or "")
    if dry_run:
        job = ImportJob(
            user_id=current_user.id,
            source_type=parsed_source_type,
            status="previewed",
            summary=_source_summary(content, parsed_source_type, file.filename or "", len(candidates)),
            completed_at=_utcnow(),
        )
        db.add(job)
        await db.commit()
        return {
            "import_job_id": job.id,
            "source_type": parsed_source_type,
            "candidates": candidates,
            "total": len(candidates),
            "sensitive_values_redacted": True,
        }
    selected = _parse_selected_ids(selected_ids, candidates)
    return await _commit_candidates(
        db,
        current_user=current_user,
        source_type=parsed_source_type,
        filename=file.filename or "",
        content=content,
        candidates=candidates,
        selected_ids=selected,
        conflict_strategy=conflict_strategy.lower().strip(),
        target_group_id=target_group_id,
    )
