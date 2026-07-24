"""Flaky test detection and quarantine service."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import FlakyDetectionConfig, FlakyTestRecord


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FlakyDetectionService:
    async def get_or_create_config(self, db: AsyncSession, project_id: int) -> FlakyDetectionConfig:
        config = await db.scalar(select(FlakyDetectionConfig).where(FlakyDetectionConfig.project_id == project_id))
        if config:
            return config
        config = FlakyDetectionConfig(project_id=project_id)
        db.add(config)
        await db.flush()
        return config

    def calculate_flaky_score(self, recent_results: list[dict[str, Any]], window_size: int = 20) -> float:
        if len(recent_results) < 3:
            return 0.0
        results = recent_results[-window_size:]
        statuses = [str(item.get("status") or "") for item in results]
        transitions = sum(1 for i in range(1, len(statuses)) if statuses[i] != statuses[i - 1])
        transition_rate = transitions / max(1, len(statuses) - 1)

        fail_rate = statuses.count("failed") / max(1, len(statuses))
        if fail_rate in (0, 1):
            entropy = 0.0
        else:
            entropy = -(fail_rate * math.log2(fail_rate) + (1 - fail_rate) * math.log2(1 - fail_rate))

        weighted_transitions = 0.0
        for i in range(1, len(statuses)):
            if statuses[i] != statuses[i - 1]:
                weighted_transitions += 1 + (i / len(statuses))
        max_weighted = sum(1 + (i / len(statuses)) for i in range(1, len(statuses))) or 1
        weighted_transition_rate = weighted_transitions / max_weighted

        score = 0.4 * transition_rate + 0.3 * entropy + 0.3 * weighted_transition_rate
        return round(min(1.0, score), 4)

    def classify(self, score: float, config: FlakyDetectionConfig, fail_rate: float = 0.0) -> str:
        if score >= config.flaky_high_threshold:
            return "flaky_high"
        if score >= config.flaky_low_threshold:
            return "flaky_low"
        if fail_rate >= 0.8:
            return "stable_fail"
        return "stable_pass"

    async def record_result(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        case_type: str,
        case_id: int,
        case_name: str,
        status: str,
        run_id: int | None = None,
    ) -> FlakyTestRecord:
        config = await self.get_or_create_config(db, project_id)
        record = await db.scalar(
            select(FlakyTestRecord).where(
                FlakyTestRecord.project_id == project_id,
                FlakyTestRecord.case_type == case_type,
                FlakyTestRecord.case_id == case_id,
            )
        )
        if record is None:
            record = FlakyTestRecord(
                project_id=project_id,
                case_type=case_type,
                case_id=case_id,
                case_name=case_name,
                recent_results=[],
            )
            db.add(record)

        normalized = (
            "passed"
            if status in {"passed", "pass", "success"}
            else "failed"
            if status
            in {
                "failed",
                "fail",
                "error",
                "infra_error",
                "timed_out",
            }
            else status
        )
        history = list(record.recent_results or [])
        previous = history[-1]["status"] if history else None
        history.append({"run_id": run_id, "status": normalized, "at": _utcnow().isoformat()})
        history = history[-max(5, config.window_size) :]
        record.recent_results = history
        record.case_name = case_name or record.case_name
        record.total_runs = int(record.total_runs or 0) + 1
        if normalized == "passed":
            record.pass_count = int(record.pass_count or 0) + 1
        elif normalized == "failed":
            record.fail_count = int(record.fail_count or 0) + 1
        if previous and previous != normalized:
            record.status_changes = int(record.status_changes or 0) + 1
            record.last_status_change_at = _utcnow()

        score = self.calculate_flaky_score(history, config.window_size)
        fail_rate = (record.fail_count or 0) / max(1, (record.pass_count or 0) + (record.fail_count or 0))
        record.flaky_score = score
        record.classification = self.classify(score, config, fail_rate)
        record.updated_at = _utcnow()

        if config.auto_quarantine and score >= config.auto_quarantine_score and not record.is_quarantined:
            record.is_quarantined = True
            record.quarantined_at = _utcnow()
        await db.flush()
        return record

    async def list_records(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        classification: str | None = None,
        quarantined: bool | None = None,
    ) -> list[FlakyTestRecord]:
        stmt = select(FlakyTestRecord).where(FlakyTestRecord.project_id == project_id)
        if classification:
            stmt = stmt.where(FlakyTestRecord.classification == classification)
        if quarantined is not None:
            stmt = stmt.where(FlakyTestRecord.is_quarantined.is_(quarantined))
        return list((await db.scalars(stmt.order_by(FlakyTestRecord.flaky_score.desc()))).all())

    async def set_quarantine(
        self,
        db: AsyncSession,
        record_id: int,
        *,
        quarantined: bool,
        user_id: int,
    ) -> FlakyTestRecord:
        record = await db.get(FlakyTestRecord, record_id)
        if record is None:
            raise LookupError("flaky record not found")
        record.is_quarantined = quarantined
        record.quarantined_by = user_id if quarantined else None
        record.quarantined_at = _utcnow() if quarantined else None
        record.updated_at = _utcnow()
        await db.flush()
        return record


flaky_detection_service = FlakyDetectionService()
