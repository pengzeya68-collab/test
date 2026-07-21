"""Secure resumable uploads for execution artifacts."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.models.autotest import ArtifactManifest, ArtifactUploadSession, AutomationExecution
from fastapi_backend.models.models import User

router = APIRouter(prefix="/api/auto-test/artifacts", tags=["Execution Artifacts"])

_MAX_ARTIFACT_BYTES = 100 * 1024 * 1024
_SESSION_TTL = timedelta(hours=2)
_ALLOWED_KINDS = {"screenshot", "trace", "video", "har", "report", "log", "dom_snapshot"}
_RANGE_RE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


def _storage_root() -> Path:
    configured = os.getenv("TESTMASTER_DATA_DIR")
    root = Path(configured) if configured else Path(__file__).resolve().parent.parent / "autotest_data"
    return root / "artifacts"


def _safe_filename(value: Any) -> str:
    name = str(value or "").strip()
    if (
        not name
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
        or Path(name).name != name
        or any(char in name for char in '<>:"/\\|?*')
    ):
        raise HTTPException(status_code=422, detail="产物文件名不合法")
    return name[:500]


def _validate_sha256(value: Any) -> str:
    digest = str(value or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise HTTPException(status_code=422, detail="SHA-256 格式不正确")
    return digest


async def _execution_for_user(db: AsyncSession, public_id: str, user_id: int) -> AutomationExecution:
    execution = await db.scalar(
        select(AutomationExecution).where(
            AutomationExecution.public_id == public_id,
            AutomationExecution.user_id == user_id,
        )
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="执行记录不存在或无权访问")
    return execution


def _upload_path(session: ArtifactUploadSession) -> Path:
    return _storage_root() / "tmp" / session.temp_storage_key


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_object_path(storage_key: str) -> Path:
    """Resolve a manifest key without allowing a corrupt row to escape artifact storage."""
    objects_root = (_storage_root() / "objects").resolve()
    candidate = (objects_root / storage_key).resolve()
    if candidate != objects_root and objects_root not in candidate.parents:
        raise HTTPException(status_code=404, detail="产物存储路径无效")
    return candidate


def _is_expired(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value < datetime.now(timezone.utc)


async def create_execution_upload_session(
    db: AsyncSession,
    *,
    execution: AutomationExecution,
    user_id: int,
    body: dict[str, Any],
    chunk_endpoint: str | None = None,
) -> dict[str, Any]:
    """Create an owner-scoped upload session for an already authorized execution."""
    kind = str(body.get("kind") or "").strip()
    if kind not in _ALLOWED_KINDS:
        raise HTTPException(status_code=422, detail="不支持的产物类型")
    try:
        expected_size = int(body.get("size_bytes"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="产物大小不正确") from exc
    if expected_size <= 0 or expected_size > _MAX_ARTIFACT_BYTES:
        raise HTTPException(status_code=422, detail=f"产物大小必须在 1 到 {_MAX_ARTIFACT_BYTES} 字节之间")

    upload_id = uuid.uuid4().hex
    session = ArtifactUploadSession(
        id=upload_id,
        execution_id=execution.id,
        user_id=user_id,
        kind=kind,
        filename=_safe_filename(body.get("filename")),
        content_type=str(body.get("content_type") or "application/octet-stream")[:200],
        expected_size_bytes=expected_size,
        expected_sha256=_validate_sha256(body.get("sha256")),
        temp_storage_key=f"{upload_id}.part",
        expires_at=datetime.now(timezone.utc) + _SESSION_TTL,
    )
    db.add(session)
    await db.commit()
    return {
        "upload_id": upload_id,
        "offset": 0,
        "expires_at": session.expires_at,
        "chunk_endpoint": chunk_endpoint or f"/api/auto-test/artifacts/upload-sessions/{upload_id}/content",
    }


async def write_execution_upload_chunk(
    db: AsyncSession,
    *,
    upload_id: str,
    user_id: int,
    request: Request,
    content_range: str | None,
    execution_id: int | None = None,
) -> None:
    """Append one validated chunk, optionally binding it to one execution."""
    match = _RANGE_RE.fullmatch(content_range or "")
    if match is None:
        raise HTTPException(status_code=422, detail="Content-Range 必须为 bytes start-end/total")
    start, end, total = (int(value) for value in match.groups())
    if end < start:
        raise HTTPException(status_code=422, detail="Content-Range 范围不合法")
    session = await db.scalar(
        select(ArtifactUploadSession).where(ArtifactUploadSession.id == upload_id).with_for_update()
    )
    if (
        session is None
        or session.user_id != user_id
        or (execution_id is not None and session.execution_id != execution_id)
    ):
        raise HTTPException(status_code=404, detail="上传会话不存在或无权访问")
    if session.status != "open":
        raise HTTPException(status_code=409, detail="上传会话不可继续写入")
    if _is_expired(session.expires_at):
        session.status = "expired"
        await db.commit()
        raise HTTPException(status_code=410, detail="上传会话已过期")
    if total != session.expected_size_bytes or start != session.received_bytes:
        raise HTTPException(status_code=409, detail="上传偏移与服务端状态不一致")

    path = _upload_path(session)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        actual_size = path.stat().st_size
        if actual_size < session.received_bytes:
            session.status = "failed"
            await db.commit()
            raise HTTPException(status_code=409, detail="上传临时文件已损坏，请重新创建上传会话")
        if actual_size > session.received_bytes:
            with path.open("r+b") as target:
                target.truncate(session.received_bytes)
    elif session.received_bytes:
        session.status = "failed"
        await db.commit()
        raise HTTPException(status_code=409, detail="上传临时文件丢失，请重新创建上传会话")
    written = 0
    try:
        with path.open("ab") as target:
            async for chunk in request.stream():
                written += len(chunk)
                if session.received_bytes + written > session.expected_size_bytes:
                    raise HTTPException(status_code=413, detail="上传内容超过声明大小")
                target.write(chunk)
    except HTTPException:
        if path.exists():
            with path.open("r+b") as target:
                target.truncate(session.received_bytes)
        raise
    except OSError as exc:
        raise HTTPException(status_code=507, detail="产物临时存储不可写") from exc

    if written != end - start + 1:
        if path.exists():
            with path.open("r+b") as target:
                target.truncate(session.received_bytes)
        raise HTTPException(status_code=422, detail="上传内容长度与 Content-Range 不一致")
    session.received_bytes += written
    await db.commit()


async def finalize_execution_upload_session(
    db: AsyncSession,
    *,
    upload_id: str,
    user_id: int,
    execution_id: int | None = None,
) -> dict[str, Any]:
    """Verify and finalize one upload, optionally binding it to one execution."""
    session = await db.scalar(
        select(ArtifactUploadSession).where(ArtifactUploadSession.id == upload_id).with_for_update()
    )
    if (
        session is None
        or session.user_id != user_id
        or (execution_id is not None and session.execution_id != execution_id)
    ):
        raise HTTPException(status_code=404, detail="上传会话不存在或无权访问")
    if session.status == "completed":
        existing = await db.scalar(
            select(ArtifactManifest).where(
                ArtifactManifest.execution_id == session.execution_id,
                ArtifactManifest.sha256 == session.expected_sha256,
            )
        )
        if existing is not None:
            return {"artifact_id": existing.id, "deduplicated": True}
    if session.status != "open":
        raise HTTPException(status_code=409, detail="上传会话不可完成")
    if _is_expired(session.expires_at):
        session.status = "expired"
        await db.commit()
        raise HTTPException(status_code=410, detail="上传会话已过期")
    if session.received_bytes != session.expected_size_bytes:
        raise HTTPException(status_code=409, detail="产物尚未上传完成")
    source = _upload_path(session)
    if not source.exists() or source.stat().st_size != session.expected_size_bytes:
        raise HTTPException(status_code=409, detail="临时文件与上传记录不一致")
    actual_hash = _hash_file(source)
    if actual_hash != session.expected_sha256:
        session.status = "failed"
        await db.commit()
        raise HTTPException(status_code=422, detail="产物 SHA-256 校验失败")

    existing = await db.scalar(
        select(ArtifactManifest).where(
            ArtifactManifest.execution_id == session.execution_id,
            ArtifactManifest.sha256 == actual_hash,
        )
    )
    if existing is not None:
        session.status = "completed"
        await db.commit()
        return {"artifact_id": existing.id, "deduplicated": True}

    storage_key = f"{session.execution_id}/{uuid.uuid4().hex}/{session.filename}"
    destination = _storage_root() / "objects" / storage_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
    artifact = ArtifactManifest(
        execution_id=session.execution_id,
        kind=session.kind,
        filename=session.filename,
        content_type=session.content_type,
        size_bytes=session.expected_size_bytes,
        sha256=actual_hash,
        storage_key=storage_key,
        retention_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(artifact)
    session.status = "completed"
    await db.commit()
    await db.refresh(artifact)
    return {"artifact_id": artifact.id, "deduplicated": False}


@router.post("/upload-sessions", status_code=status.HTTP_201_CREATED)
async def create_upload_session(
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("suite:execute")),
    db: AsyncSession = Depends(get_autotest_db),
):
    execution = await _execution_for_user(db, str(body.get("execution_id") or ""), current_user.id)
    return await create_execution_upload_session(
        db,
        execution=execution,
        user_id=current_user.id,
        body=body,
    )


@router.get("/upload-sessions/{upload_id}")
async def get_upload_session_progress(
    upload_id: str,
    current_user: User = Depends(require_permissions("suite:execute")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """Return the authoritative resumable-upload offset without exposing paths."""
    session = await db.scalar(
        select(ArtifactUploadSession).where(
            ArtifactUploadSession.id == upload_id,
            ArtifactUploadSession.user_id == current_user.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="上传会话不存在或无权访问")
    return {
        "upload_id": session.id,
        "status": session.status,
        "received_bytes": session.received_bytes,
        "size_bytes": session.expected_size_bytes,
        "expires_at": session.expires_at,
    }


@router.put("/upload-sessions/{upload_id}/content", status_code=status.HTTP_204_NO_CONTENT)
async def upload_artifact_chunk(
    upload_id: str,
    request: Request,
    content_range: str | None = Header(default=None, alias="Content-Range"),
    current_user: User = Depends(require_permissions("suite:execute")),
    db: AsyncSession = Depends(get_autotest_db),
):
    await write_execution_upload_chunk(
        db,
        upload_id=upload_id,
        user_id=current_user.id,
        request=request,
        content_range=content_range,
    )


@router.post("/upload-sessions/{upload_id}/complete")
async def complete_upload_session(
    upload_id: str,
    current_user: User = Depends(require_permissions("suite:execute")),
    db: AsyncSession = Depends(get_autotest_db),
):
    return await finalize_execution_upload_session(
        db,
        upload_id=upload_id,
        user_id=current_user.id,
    )


@router.get("/executions/{execution_id}")
async def list_execution_artifacts(
    execution_id: str,
    current_user: User = Depends(require_permissions("artifact:download")),
    db: AsyncSession = Depends(get_autotest_db),
):
    execution = await _execution_for_user(db, execution_id, current_user.id)
    artifacts = list(
        (
            await db.scalars(
                select(ArtifactManifest)
                .where(ArtifactManifest.execution_id == execution.id)
                .order_by(ArtifactManifest.created_at)
            )
        ).all()
    )
    return {
        "artifacts": [
            {
                "id": artifact.id,
                "kind": artifact.kind,
                "filename": artifact.filename,
                "content_type": artifact.content_type,
                "size_bytes": artifact.size_bytes,
                "sha256": artifact.sha256,
                "retention_until": artifact.retention_until,
                "created_at": artifact.created_at,
            }
            for artifact in artifacts
        ]
    }


@router.get("/{artifact_id}/content")
@audit_log("download", "artifact", resource_id_param="artifact_id")
async def download_artifact(
    artifact_id: int,
    current_user: User = Depends(require_permissions("artifact:download")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """Stream an artifact after ownership, retention and storage checks."""
    artifact = await db.scalar(
        select(ArtifactManifest)
        .join(AutomationExecution, ArtifactManifest.execution_id == AutomationExecution.id)
        .where(
            ArtifactManifest.id == artifact_id,
            AutomationExecution.user_id == current_user.id,
        )
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="产物不存在或无权访问")
    if artifact.retention_until and _is_expired(artifact.retention_until):
        raise HTTPException(status_code=410, detail="产物已超过保留期限")
    path = _artifact_object_path(artifact.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="产物文件不存在")
    if path.stat().st_size != artifact.size_bytes:
        raise HTTPException(status_code=409, detail="产物文件与清单不一致")
    return FileResponse(
        path,
        media_type=artifact.content_type or "application/octet-stream",
        filename=artifact.filename,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )
