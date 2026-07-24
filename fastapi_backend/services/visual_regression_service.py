"""Visual regression comparison service."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import (
    DiffVerdict,
    VisualBaseline,
    VisualComparison,
    VisualComparisonConfig,
    VisualMaskRegion,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ComparisonResult:
    diff_percentage: float
    mismatched_pixels: int
    total_pixels: int
    diff_image_path: str | None
    verdict: str
    image_hash: str


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class VisualRegressionService:
    def __init__(self, artifact_root: str | Path | None = None):
        self.artifact_root = Path(artifact_root or os.getenv("TESTMASTER_ARTIFACT_ROOT", "instance/artifacts"))
        self.artifact_root.mkdir(parents=True, exist_ok=True)

    async def get_or_create_config(self, db: AsyncSession, project_id: int) -> VisualComparisonConfig:
        config = await db.scalar(select(VisualComparisonConfig).where(VisualComparisonConfig.project_id == project_id))
        if config:
            return config
        config = VisualComparisonConfig(project_id=project_id)
        db.add(config)
        await db.flush()
        return config

    async def list_baselines(
        self,
        db: AsyncSession,
        *,
        project_id: int | None = None,
        step_id: str | None = None,
        env_id: int | None = None,
    ) -> list[VisualBaseline]:
        stmt = select(VisualBaseline).order_by(VisualBaseline.updated_at.desc())
        if project_id is not None:
            stmt = stmt.where(VisualBaseline.project_id == project_id)
        if step_id is not None:
            stmt = stmt.where(VisualBaseline.ui_step_id == step_id)
        if env_id is not None:
            stmt = stmt.where(VisualBaseline.environment_id == env_id)
        return list((await db.scalars(stmt)).all())

    async def create_baseline(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        ui_step_id: str,
        image_path: str,
        user_id: int,
        environment_id: int | None = None,
        browser_engine: str = "chromium",
        viewport_width: int = 1280,
        viewport_height: int = 720,
        run_id: int | None = None,
        step_result_id: int | None = None,
        activate: bool = True,
    ) -> VisualBaseline:
        image = Path(image_path)
        if not image.is_file():
            raise FileNotFoundError(f"baseline image not found: {image_path}")

        width, height = self._image_size(image)
        image_hash = file_sha256(image)
        stored = self._store_image(image, project_id, "baselines")

        existing = list(
            (
                await db.scalars(
                    select(VisualBaseline).where(
                        VisualBaseline.ui_step_id == ui_step_id,
                        VisualBaseline.environment_id == environment_id,
                        VisualBaseline.browser_engine == browser_engine,
                        VisualBaseline.viewport_width == viewport_width,
                        VisualBaseline.viewport_height == viewport_height,
                        VisualBaseline.status == "active",
                    )
                )
            ).all()
        )
        next_version = 1
        for item in existing:
            next_version = max(next_version, int(item.version or 1) + 1)
            if activate:
                item.status = "superseded"

        baseline = VisualBaseline(
            project_id=project_id,
            ui_step_id=ui_step_id,
            environment_id=environment_id,
            browser_engine=browser_engine,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            image_path=str(stored),
            image_hash=image_hash,
            image_width=width,
            image_height=height,
            status="active" if activate else "pending",
            version=next_version,
            captured_from_run_id=run_id,
            captured_from_step_result_id=step_result_id,
            created_by=user_id,
        )
        db.add(baseline)
        await db.flush()
        return baseline

    async def add_mask(
        self,
        db: AsyncSession,
        *,
        baseline_id: int,
        name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        user_id: int,
        shape: str = "rect",
    ) -> VisualMaskRegion:
        baseline = await db.get(VisualBaseline, baseline_id)
        if baseline is None:
            raise LookupError("baseline not found")
        mask = VisualMaskRegion(
            baseline_id=baseline_id,
            name=name,
            x=max(0.0, min(1.0, x)),
            y=max(0.0, min(1.0, y)),
            width=max(0.0, min(1.0, width)),
            height=max(0.0, min(1.0, height)),
            shape=shape or "rect",
            created_by=user_id,
        )
        db.add(mask)
        await db.flush()
        return mask

    async def compare_images(
        self,
        baseline_path: str,
        actual_path: str,
        *,
        mask_regions: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
        output_dir: Path | None = None,
    ) -> ComparisonResult:
        config = config or {}
        baseline_hash = file_sha256(baseline_path)
        actual_hash = file_sha256(actual_path)
        if baseline_hash == actual_hash:
            return ComparisonResult(
                diff_percentage=0.0,
                mismatched_pixels=0,
                total_pixels=1,
                diff_image_path=None,
                verdict=DiffVerdict.auto_passed.value,
                image_hash=actual_hash,
            )

        try:
            from PIL import Image
            import numpy as np
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError("Pillow/numpy required for visual comparison") from exc

        baseline_img = Image.open(baseline_path).convert("RGB")
        actual_img = Image.open(actual_path).convert("RGB")
        if baseline_img.size != actual_img.size:
            actual_img = actual_img.resize(baseline_img.size, Image.Resampling.LANCZOS)

        baseline_arr = np.array(baseline_img)
        actual_arr = np.array(actual_img)
        for mask in mask_regions or []:
            x, y, w, h = self._to_pixel_coords(mask, baseline_img.size)
            baseline_arr[y : y + h, x : x + w] = 0
            actual_arr[y : y + h, x : x + w] = 0

        diff = np.abs(baseline_arr.astype("int16") - actual_arr.astype("int16"))
        magnitude = diff.sum(axis=2)
        threshold_per_pixel = int(config.get("pixel_tolerance", 30))
        mismatched = magnitude > threshold_per_pixel
        mismatched_pixels = int(mismatched.sum())
        total_pixels = int(baseline_arr.shape[0] * baseline_arr.shape[1]) or 1
        diff_percentage = (mismatched_pixels / total_pixels) * 100.0

        heat = baseline_arr.copy()
        heat[mismatched] = (0.7 * baseline_arr[mismatched] + 0.3 * np.array([255, 0, 0], dtype="float32")).astype(
            "uint8"
        )
        out_dir = output_dir or (self.artifact_root / "visual-diff")
        out_dir.mkdir(parents=True, exist_ok=True)
        diff_path = out_dir / f"diff-{actual_hash[:12]}-{int(_utcnow().timestamp())}.png"
        Image.fromarray(heat).save(diff_path)

        auto_approve = float(config.get("auto_approve_below", 0.01))
        threshold = float(config.get("threshold", 0.1))
        auto_reject = float(config.get("auto_reject_above", 5.0))
        if diff_percentage <= auto_approve or diff_percentage <= threshold:
            verdict = DiffVerdict.auto_passed.value
        elif diff_percentage >= auto_reject:
            # High-diff is treated as rejected (bug candidate) for automation gates.
            verdict = DiffVerdict.rejected.value
        else:
            verdict = DiffVerdict.pending.value

        return ComparisonResult(
            diff_percentage=round(diff_percentage, 4),
            mismatched_pixels=mismatched_pixels,
            total_pixels=total_pixels,
            diff_image_path=str(diff_path),
            verdict=verdict,
            image_hash=actual_hash,
        )

    async def compare_and_persist(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        run_id: int,
        actual_image_path: str,
        ui_step_id: str | None = None,
        step_result_id: int | None = None,
        environment_id: int | None = None,
        browser_engine: str = "chromium",
        viewport_width: int = 1280,
        viewport_height: int = 720,
        user_id: int | None = None,
        create_baseline_if_missing: bool = True,
    ) -> VisualComparison:
        config = await self.get_or_create_config(db, project_id)
        baseline = None
        if ui_step_id:
            baseline = await db.scalar(
                select(VisualBaseline)
                .where(
                    VisualBaseline.ui_step_id == ui_step_id,
                    VisualBaseline.environment_id == environment_id,
                    VisualBaseline.browser_engine == browser_engine,
                    VisualBaseline.viewport_width == viewport_width,
                    VisualBaseline.viewport_height == viewport_height,
                    VisualBaseline.status == "active",
                )
                .order_by(VisualBaseline.version.desc())
            )

        if baseline is None:
            if create_baseline_if_missing and ui_step_id and user_id is not None:
                baseline = await self.create_baseline(
                    db,
                    project_id=project_id,
                    ui_step_id=ui_step_id,
                    image_path=actual_image_path,
                    user_id=user_id,
                    environment_id=environment_id,
                    browser_engine=browser_engine,
                    viewport_width=viewport_width,
                    viewport_height=viewport_height,
                    run_id=run_id,
                    step_result_id=step_result_id,
                    activate=False,
                )
                comparison = VisualComparison(
                    project_id=project_id,
                    run_id=run_id,
                    step_result_id=step_result_id,
                    ui_step_id=ui_step_id,
                    baseline_id=baseline.id,
                    actual_image_path=actual_image_path,
                    diff_image_path=None,
                    diff_percentage=0.0,
                    threshold=config.default_threshold,
                    mismatched_pixels=0,
                    total_pixels=0,
                    verdict=DiffVerdict.pending.value,
                    config_snapshot={
                        "threshold": config.default_threshold,
                        "note": "baseline_created_pending_approval",
                    },
                )
                db.add(comparison)
                await db.flush()
                return comparison

            comparison = VisualComparison(
                project_id=project_id,
                run_id=run_id,
                step_result_id=step_result_id,
                ui_step_id=ui_step_id,
                baseline_id=None,
                actual_image_path=actual_image_path,
                diff_percentage=0.0,
                threshold=config.default_threshold,
                mismatched_pixels=0,
                total_pixels=0,
                verdict=DiffVerdict.no_baseline.value,
                config_snapshot={"threshold": config.default_threshold},
            )
            db.add(comparison)
            await db.flush()
            return comparison

        masks = list(
            (await db.scalars(select(VisualMaskRegion).where(VisualMaskRegion.baseline_id == baseline.id))).all()
        )
        result = await self.compare_images(
            baseline.image_path,
            actual_image_path,
            mask_regions=[{"x": m.x, "y": m.y, "width": m.width, "height": m.height, "shape": m.shape} for m in masks],
            config={
                "threshold": config.default_threshold,
                "auto_approve_below": config.auto_approve_below,
                "auto_reject_above": config.auto_reject_above,
                "antialiasing_tolerance": config.antialiasing_tolerance,
            },
        )
        comparison = VisualComparison(
            project_id=project_id,
            run_id=run_id,
            step_result_id=step_result_id,
            ui_step_id=ui_step_id,
            baseline_id=baseline.id,
            actual_image_path=actual_image_path,
            diff_image_path=result.diff_image_path,
            diff_percentage=result.diff_percentage,
            threshold=config.default_threshold,
            mismatched_pixels=result.mismatched_pixels,
            total_pixels=result.total_pixels,
            verdict=result.verdict,
            config_snapshot={
                "threshold": config.default_threshold,
                "auto_approve_below": config.auto_approve_below,
                "auto_reject_above": config.auto_reject_above,
                "mask_count": len(masks),
            },
        )
        db.add(comparison)
        await db.flush()
        return comparison

    async def list_comparisons(
        self,
        db: AsyncSession,
        *,
        project_id: int | None = None,
        run_id: int | None = None,
        verdict: str | None = None,
        limit: int = 100,
    ) -> list[VisualComparison]:
        stmt = select(VisualComparison).order_by(VisualComparison.created_at.desc()).limit(max(1, min(limit, 500)))
        if project_id is not None:
            stmt = stmt.where(VisualComparison.project_id == project_id)
        if run_id is not None:
            stmt = stmt.where(VisualComparison.run_id == run_id)
        if verdict is not None:
            stmt = stmt.where(VisualComparison.verdict == verdict)
        return list((await db.scalars(stmt)).all())

    async def get_comparison(self, db: AsyncSession, comparison_id: int) -> VisualComparison:
        comparison = await db.get(VisualComparison, comparison_id)
        if comparison is None:
            raise LookupError("comparison not found")
        return comparison

    async def update_config(
        self,
        db: AsyncSession,
        project_id: int,
        payload: dict[str, Any],
    ) -> VisualComparisonConfig:
        config = await self.get_or_create_config(db, project_id)
        for key in (
            "default_threshold",
            "antialiasing_tolerance",
            "auto_approve_below",
            "auto_reject_above",
            "default_engine",
            "capture_full_page",
        ):
            if key in payload and payload[key] is not None:
                setattr(config, key, payload[key])
        config.updated_at = _utcnow()
        await db.flush()
        return config

    async def stats(self, db: AsyncSession, project_id: int) -> dict[str, Any]:
        items = list(
            (
                await db.scalars(
                    select(VisualComparison)
                    .where(VisualComparison.project_id == project_id)
                    .order_by(VisualComparison.created_at.desc())
                    .limit(500)
                )
            ).all()
        )
        by_verdict: dict[str, int] = {}
        for item in items:
            by_verdict[item.verdict] = by_verdict.get(item.verdict, 0) + 1
        baselines = await self.list_baselines(db, project_id=project_id)
        active = sum(1 for b in baselines if b.status == "active")
        return {
            "comparison_count": len(items),
            "by_verdict": by_verdict,
            "baseline_count": len(baselines),
            "active_baselines": active,
            "pending_reviews": by_verdict.get(DiffVerdict.pending.value, 0),
        }

    async def list_masks(self, db: AsyncSession, baseline_id: int) -> list[VisualMaskRegion]:
        return list(
            (await db.scalars(select(VisualMaskRegion).where(VisualMaskRegion.baseline_id == baseline_id))).all()
        )

    async def set_verdict(
        self,
        db: AsyncSession,
        comparison_id: int,
        *,
        verdict: str,
        user_id: int,
        comment: str | None = None,
        promote_baseline: bool = False,
    ) -> VisualComparison:
        comparison = await db.get(VisualComparison, comparison_id)
        if comparison is None:
            raise LookupError("comparison not found")
        if comparison.verdict not in (DiffVerdict.pending.value, DiffVerdict.no_baseline.value):
            # optimistic concurrency: only pending can be decided once
            if comparison.verdict != verdict:
                raise ValueError("comparison already decided")
            return comparison
        if verdict not in {DiffVerdict.approved.value, DiffVerdict.rejected.value, DiffVerdict.auto_passed.value}:
            raise ValueError("invalid verdict")
        comparison.verdict = verdict
        comparison.verdict_by = user_id
        comparison.verdict_at = _utcnow()
        comparison.verdict_comment = comment
        if promote_baseline and verdict == DiffVerdict.approved.value and comparison.ui_step_id:
            await self.create_baseline(
                db,
                project_id=comparison.project_id,
                ui_step_id=comparison.ui_step_id,
                image_path=comparison.actual_image_path,
                user_id=user_id,
                run_id=comparison.run_id,
                step_result_id=comparison.step_result_id,
                activate=True,
            )
        await db.flush()
        return comparison

    def _store_image(self, source: Path, project_id: int, kind: str) -> Path:
        target_dir = self.artifact_root / "visual" / str(project_id) / kind
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{source.stem}-{file_sha256(source)[:12]}{source.suffix or '.png'}"
        if not target.exists():
            target.write_bytes(source.read_bytes())
        return target

    def _image_size(self, path: Path) -> tuple[int, int]:
        try:
            from PIL import Image

            with Image.open(path) as img:
                return int(img.width), int(img.height)
        except Exception:
            return 0, 0

    def _to_pixel_coords(self, mask: dict[str, Any], size: tuple[int, int]) -> tuple[int, int, int, int]:
        width, height = size
        x = int(float(mask.get("x", 0)) * width)
        y = int(float(mask.get("y", 0)) * height)
        w = max(1, int(float(mask.get("width", 0)) * width))
        h = max(1, int(float(mask.get("height", 0)) * height))
        return x, y, w, h


visual_regression_service = VisualRegressionService()
