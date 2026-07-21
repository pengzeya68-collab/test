"""Retention cleanup for resumable artifact uploads and completed artifacts."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.models.autotest import ArtifactManifest, ArtifactUploadSession

_logger = logging.getLogger(__name__)
_CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60
_COMPLETED_SESSION_RETENTION = timedelta(days=7)
_cleanup_task: asyncio.Task[None] | None = None


def artifact_storage_root() -> Path:
    configured = os.getenv("TESTMASTER_DATA_DIR")
    root = Path(configured) if configured else Path(__file__).resolve().parent.parent / "autotest_data"
    return root / "artifacts"


def _object_path(root: Path, storage_key: str) -> Path | None:
    objects_root = (root / "objects").resolve()
    candidate = (objects_root / storage_key).resolve()
    if candidate == objects_root or objects_root not in candidate.parents:
        return None
    return candidate


def _temporary_path(root: Path, storage_key: str) -> Path | None:
    filename = Path(storage_key).name
    if not filename or filename != storage_key:
        return None
    return (root / "tmp" / filename).resolve()


async def cleanup_expired_artifacts(
    session_factory: Any = None,
    storage_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, int]:
    """Remove expired local files and their metadata without escaping storage roots."""
    current_time = now or datetime.now(timezone.utc)
    root = storage_root or artifact_storage_root()
    factory = session_factory or AsyncSessionLocal
    result = {"expired_uploads": 0, "deleted_upload_records": 0, "deleted_artifacts": 0}

    async with factory() as db:  # type: AsyncSession
        expired_uploads = list(
            (
                await db.scalars(
                    select(ArtifactUploadSession).where(
                        ArtifactUploadSession.status == "open",
                        ArtifactUploadSession.expires_at < current_time,
                    )
                )
            ).all()
        )
        for upload in expired_uploads:
            path = _temporary_path(root, upload.temp_storage_key)
            if path is not None:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    _logger.warning("Unable to remove expired artifact upload %s: %s", upload.id, exc)
                    continue
            upload.status = "expired"
            result["expired_uploads"] += 1

        old_sessions = list(
            (
                await db.scalars(
                    select(ArtifactUploadSession).where(
                        ArtifactUploadSession.status.in_(("completed", "failed", "expired")),
                        ArtifactUploadSession.expires_at < current_time - _COMPLETED_SESSION_RETENTION,
                    )
                )
            ).all()
        )
        for upload in old_sessions:
            path = _temporary_path(root, upload.temp_storage_key)
            if path is not None:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    _logger.warning("Unable to remove stale upload file %s: %s", upload.id, exc)
                    continue
            await db.delete(upload)
            result["deleted_upload_records"] += 1

        expired_manifests = list(
            (
                await db.scalars(
                    select(ArtifactManifest).where(
                        ArtifactManifest.retention_until.is_not(None),
                        ArtifactManifest.retention_until < current_time,
                    )
                )
            ).all()
        )
        for artifact in expired_manifests:
            path = _object_path(root, artifact.storage_key)
            if path is None:
                _logger.warning("Skipping artifact %s with an unsafe storage key", artifact.id)
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                _logger.warning("Unable to remove expired artifact %s: %s", artifact.id, exc)
                continue
            await db.delete(artifact)
            result["deleted_artifacts"] += 1
        await db.commit()
    return result


async def _run_cleanup_loop() -> None:
    while True:
        try:
            await cleanup_expired_artifacts()
        except asyncio.CancelledError:
            raise
        except Exception:
            _logger.exception("Artifact retention cleanup failed")
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)


async def start_artifact_maintenance() -> None:
    """Run one cleanup during startup and retain the periodic task strongly."""
    global _cleanup_task
    await cleanup_expired_artifacts()
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_run_cleanup_loop(), name="artifact-retention-cleanup")


async def stop_artifact_maintenance() -> None:
    global _cleanup_task
    task = _cleanup_task
    _cleanup_task = None
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
