"""Post-run upgrade pipeline: auto register traces + visual comparisons from artifacts."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.autotest import ArtifactManifest
from fastapi_backend.models.ui_automation import UIArtifact, UIRun, UIStepResult

logger = logging.getLogger(__name__)


def artifact_storage_root() -> Path:
    configured = os.getenv("TESTMASTER_DATA_DIR")
    root = Path(configured) if configured else Path(__file__).resolve().parent.parent / "autotest_data"
    return root / "artifacts"


def resolve_manifest_path(manifest: ArtifactManifest) -> Path | None:
    if not manifest or not manifest.storage_key:
        return None
    objects_root = (artifact_storage_root() / "objects").resolve()
    candidate = (objects_root / manifest.storage_key).resolve()
    if candidate != objects_root and objects_root not in candidate.parents:
        return None
    return candidate if candidate.is_file() else None


def _is_trace(filename: str, kind: str | None) -> bool:
    name = (filename or "").lower()
    kind_l = (kind or "").lower()
    return (
        kind_l in {"trace", "playwright-trace", "pw-trace"}
        or name.endswith(".zip")
        and ("trace" in name or name.endswith(".trace.zip"))
        or name.endswith(".trace")
    )


def _is_screenshot(filename: str, kind: str | None) -> bool:
    name = (filename or "").lower()
    kind_l = (kind or "").lower()
    if kind_l in {"screenshot", "visual", "image", "diff"}:
        return True
    return name.endswith((".png", ".jpg", ".jpeg", ".webp"))


def project_id_for_run(run: UIRun) -> int:
    """Prefer real workspace project_id; never invent user_id as project."""
    pid = getattr(run, "project_id", None)
    if pid is not None:
        try:
            value = int(pid)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
    return 0


class UpgradePipelineService:
    async def process_linked_artifact(
        self,
        db: AsyncSession,
        *,
        run: UIRun,
        artifact: UIArtifact,
        manifest: ArtifactManifest | None = None,
    ) -> dict[str, Any]:
        """Best-effort: register traces and enqueue visual compare when screenshots land."""
        result: dict[str, Any] = {"trace_id": None, "comparison_id": None, "skipped": None}
        try:
            if manifest is None and artifact.artifact_manifest_id:
                manifest = await db.get(ArtifactManifest, artifact.artifact_manifest_id)
            if manifest is None:
                result["skipped"] = "no_manifest"
                return result

            path = resolve_manifest_path(manifest)
            if path is None:
                result["skipped"] = "file_missing"
                return result

            project_id = project_id_for_run(run)
            filename = artifact.filename or manifest.filename or path.name
            kind = artifact.type or manifest.kind

            if _is_trace(filename, kind):
                from fastapi_backend.services.trace_viewer_service import trace_viewer_service

                session = await trace_viewer_service.register_trace(
                    db,
                    project_id=project_id,
                    run_id=run.id,
                    file_path=str(path),
                )
                try:
                    await trace_viewer_service.ensure_parsed(db, session.id)
                except Exception:
                    logger.exception("trace parse failed for run %s artifact %s", run.id, artifact.id)
                result["trace_id"] = session.id
                return result

            if _is_screenshot(filename, kind):
                from fastapi_backend.services.visual_regression_service import visual_regression_service

                step_result_id = None
                ui_step_id = None
                stem = Path(filename).stem
                # Precise binding from filename conventions:
                #   visual-<stepId>-... / screenshot-<stepId>-... / step-<stepId>-...
                #   stepresult-<id>-... / sr-<id>-...
                # Prefer exact step_id / step_result_id match over "latest step".
                candidates: list[str] = []
                for prefix in ("visual-", "screenshot-", "step-", "stepresult-", "sr-"):
                    if stem.lower().startswith(prefix):
                        rest = stem[len(prefix) :]
                        token = rest.split("-")[0] if rest else ""
                        if token:
                            candidates.append(token)
                        break
                # Also accept embedded tokens: ...-step-<id>-... / ...-sr-<id>-...
                lower = stem.lower()
                for marker in ("-step-", "-sr-", "-stepresult-"):
                    if marker in lower:
                        token = lower.split(marker, 1)[1].split("-")[0]
                        if token:
                            candidates.append(token)

                for token in candidates:
                    # Numeric token → step_result.id
                    if token.isdigit():
                        step = await db.scalar(
                            select(UIStepResult).where(
                                UIStepResult.run_id == run.id,
                                UIStepResult.id == int(token),
                            )
                        )
                        if step:
                            step_result_id = step.id
                            ui_step_id = step.step_id
                            break
                    # UUID / string step_id
                    step = await db.scalar(
                        select(UIStepResult).where(
                            UIStepResult.run_id == run.id,
                            UIStepResult.step_id == token,
                        )
                    )
                    if step:
                        step_result_id = step.id
                        ui_step_id = step.step_id
                        break
                    # Accept longer step_id prefixes (first 8+ chars of uuid)
                    if len(token) >= 4:
                        step = await db.scalar(
                            select(UIStepResult)
                            .where(
                                UIStepResult.run_id == run.id,
                                UIStepResult.step_id.is_not(None),
                                UIStepResult.step_id.startswith(token),
                            )
                            .order_by(UIStepResult.id.desc())
                            .limit(1)
                        )
                        if step:
                            step_result_id = step.id
                            ui_step_id = step.step_id
                            break

                # Only if filename clearly marks visual/assert AND no match: leave unbound
                # (do NOT fall back to latest step — that mis-attributes multi-step runs).
                if ui_step_id is None and not candidates:
                    logger.info(
                        "visual screenshot unbound (no step token in filename) run=%s file=%s",
                        run.id,
                        filename,
                    )

                comparison = await visual_regression_service.compare_and_persist(
                    db,
                    project_id=project_id,
                    run_id=run.id,
                    actual_image_path=str(path),
                    ui_step_id=ui_step_id,
                    step_result_id=step_result_id,
                    browser_engine=str(getattr(run, "browser_engine", None) or "chromium"),
                    user_id=run.user_id,
                    create_baseline_if_missing=True,
                )
                result["comparison_id"] = comparison.id
                return result

            result["skipped"] = "unsupported_kind"
            return result
        except Exception:
            logger.exception("upgrade pipeline failed for run %s artifact %s", run.id, getattr(artifact, "id", None))
            result["skipped"] = "error"
            return result

    async def process_run_artifacts(self, db: AsyncSession, run: UIRun) -> list[dict[str, Any]]:
        artifacts = list((await db.scalars(select(UIArtifact).where(UIArtifact.run_id == run.id))).all())
        outputs: list[dict[str, Any]] = []
        for artifact in artifacts:
            outputs.append(await self.process_linked_artifact(db, run=run, artifact=artifact))
        return outputs


upgrade_pipeline_service = UpgradePipelineService()
