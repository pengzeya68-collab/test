"""Suite sharding and parallel assignment service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import (
    AgentWorkerSlot,
    CaseConcurrencyTag,
    CaseConcurrencyTagAssignment,
    ExecutionProgress,
    SuiteShard,
)
from fastapi_backend.models.ui_automation import DesktopAgent, UIRun


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SuiteShardingService:
    def __init__(self, max_shards: int = 32):
        self.max_shards = max_shards

    async def create_shards(
        self,
        db: AsyncSession,
        *,
        suite_execution_id: int,
        case_ids: list[int],
        suite_id: int | None = None,
        strategy: str = "balanced",
        project_id: int | None = None,
        online_agent_count: int | None = None,
        avg_durations: dict[int, float] | None = None,
    ) -> list[SuiteShard]:
        if not case_ids:
            return []
        if online_agent_count is None:
            agents = list(
                (
                    await db.scalars(
                        select(DesktopAgent).where(
                            DesktopAgent.status == "online",
                            DesktopAgent.revoked_at.is_(None),
                            DesktopAgent.project_id == project_id,
                        )
                    )
                ).all()
            )
            agent_count = max(1, len(agents))
        else:
            agent_count = max(1, int(online_agent_count))
        shard_count = max(1, min(len(case_ids), max(1, agent_count) * 2, self.max_shards))

        # Always honor concurrency tags when present: exclusive / limited tags constrain
        # cross-shard parallelism. Only truly untagged free cases may be rebalanced.
        has_tag_assignments = await db.scalar(
            select(CaseConcurrencyTagAssignment.id).where(CaseConcurrencyTagAssignment.case_id.in_(case_ids)).limit(1)
        )
        if has_tag_assignments is not None or strategy == "by_tag":
            groups = await self._group_by_concurrency_tags(db, case_ids, shard_count)
            if strategy == "balanced" and avg_durations:
                tagged = await self._tagged_case_ids(db, case_ids)
                free = [cid for group in groups for cid in group if cid not in tagged]
                locked = [group for group in groups if any(cid in tagged for cid in group)]
                free_groups = (
                    self._greedy_balance(free, avg_durations, max(1, shard_count - len(locked))) if free else []
                )
                groups = [g for g in (locked + free_groups) if g]
        elif strategy == "balanced":
            groups = self._greedy_balance(case_ids, avg_durations or {}, shard_count)
        else:
            groups = self._round_robin(case_ids, shard_count)

        shards: list[SuiteShard] = []
        for index, group in enumerate(groups):
            if not group:
                continue
            shard = SuiteShard(
                suite_execution_id=suite_execution_id,
                suite_id=suite_id,
                shard_index=index,
                total_shards=len(groups),
                case_ids=group,
                total_cases=len(group),
                status="pending",
            )
            db.add(shard)
            shards.append(shard)
        progress = await db.scalar(
            select(ExecutionProgress).where(ExecutionProgress.suite_execution_id == suite_execution_id)
        )
        if progress is None:
            progress = ExecutionProgress(suite_execution_id=suite_execution_id, total_cases=len(case_ids))
            db.add(progress)
        else:
            progress.total_cases = len(case_ids)
            progress.updated_at = _utcnow()
        await db.flush()
        return shards

    async def assign_shard(self, db: AsyncSession, agent_id: int) -> SuiteShard | None:
        result = await db.execute(
            select(SuiteShard)
            .where(SuiteShard.status == "pending")
            .order_by(SuiteShard.shard_index, SuiteShard.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        shard = result.scalar_one_or_none()
        if shard is None:
            return None
        now = _utcnow()
        shard.assigned_agent_id = agent_id
        shard.status = "assigned"
        shard.assigned_at = now
        await db.flush()
        return shard

    async def mark_shard_running(self, db: AsyncSession, shard_id: int) -> SuiteShard:
        shard = await db.get(SuiteShard, shard_id)
        if shard is None:
            raise LookupError("shard not found")
        shard.status = "running"
        shard.started_at = shard.started_at or _utcnow()
        await db.flush()
        return shard

    async def update_shard_progress(
        self,
        db: AsyncSession,
        shard_id: int,
        *,
        completed_delta: int = 0,
        passed_delta: int = 0,
        failed_delta: int = 0,
        completed: bool = False,
    ) -> SuiteShard:
        shard = await db.get(SuiteShard, shard_id)
        if shard is None:
            raise LookupError("shard not found")
        shard.completed_cases = int(shard.completed_cases or 0) + completed_delta
        shard.passed_cases = int(shard.passed_cases or 0) + passed_delta
        shard.failed_cases = int(shard.failed_cases or 0) + failed_delta
        if completed or shard.completed_cases >= shard.total_cases:
            shard.status = "completed" if shard.failed_cases == 0 else "failed"
            shard.completed_at = _utcnow()
        progress = await db.scalar(
            select(ExecutionProgress).where(ExecutionProgress.suite_execution_id == shard.suite_execution_id)
        )
        if progress:
            progress.completed_cases = int(progress.completed_cases or 0) + completed_delta
            progress.passed_cases = int(progress.passed_cases or 0) + passed_delta
            progress.failed_cases = int(progress.failed_cases or 0) + failed_delta
            remaining = max(0, int(progress.total_cases or 0) - int(progress.completed_cases or 0))
            progress.estimated_remaining_ms = remaining * 30_000
            progress.updated_at = _utcnow()
        await db.flush()
        return shard

    async def handle_agent_death(self, db: AsyncSession, agent_id: int) -> list[SuiteShard]:
        shards = list(
            (
                await db.scalars(
                    select(SuiteShard).where(
                        SuiteShard.assigned_agent_id == agent_id,
                        SuiteShard.status.in_(("assigned", "running")),
                    )
                )
            ).all()
        )
        reassigned: list[SuiteShard] = []
        for shard in shards:
            completed_case_ids = await self._completed_case_ids_for_shard(db, shard)
            remaining = [case_id for case_id in (shard.case_ids or []) if case_id not in completed_case_ids]
            if not remaining:
                shard.status = "completed"
                shard.completed_at = _utcnow()
                continue
            shard.case_ids = remaining
            shard.total_cases = len(remaining)
            shard.status = "pending"
            shard.original_agent_id = agent_id
            shard.assigned_agent_id = None
            shard.reassign_count = int(shard.reassign_count or 0) + 1
            reassigned.append(shard)
        slots = list((await db.scalars(select(AgentWorkerSlot).where(AgentWorkerSlot.agent_id == agent_id))).all())
        for slot in slots:
            slot.status = "idle"
            slot.current_run_id = None
            slot.current_case_name = None
        await db.flush()
        return reassigned

    async def ensure_worker_slots(self, db: AsyncSession, agent: DesktopAgent) -> list[AgentWorkerSlot]:
        existing = list(
            (
                await db.scalars(
                    select(AgentWorkerSlot)
                    .where(AgentWorkerSlot.agent_id == agent.id)
                    .order_by(AgentWorkerSlot.slot_index)
                )
            ).all()
        )
        desired = max(1, int(agent.max_parallel or 1))
        by_index = {slot.slot_index: slot for slot in existing}
        slots: list[AgentWorkerSlot] = []
        for index in range(desired):
            slot = by_index.get(index)
            if slot is None:
                slot = AgentWorkerSlot(agent_id=agent.id, slot_index=index, status="idle")
                db.add(slot)
            slots.append(slot)
        await db.flush()
        return slots

    async def get_progress(self, db: AsyncSession, suite_execution_id: int) -> dict[str, Any]:
        progress = await db.scalar(
            select(ExecutionProgress).where(ExecutionProgress.suite_execution_id == suite_execution_id)
        )
        shards = list(
            (
                await db.scalars(
                    select(SuiteShard)
                    .where(SuiteShard.suite_execution_id == suite_execution_id)
                    .order_by(SuiteShard.shard_index)
                )
            ).all()
        )
        return {
            "total": progress.total_cases if progress else 0,
            "completed": progress.completed_cases if progress else 0,
            "passed": progress.passed_cases if progress else 0,
            "failed": progress.failed_cases if progress else 0,
            "running": progress.running_cases if progress else sum(1 for s in shards if s.status == "running"),
            "skipped": progress.skipped_cases if progress else 0,
            "eta_ms": progress.estimated_remaining_ms if progress else None,
            "shards": [
                {
                    "id": shard.id,
                    "index": shard.shard_index,
                    "status": shard.status,
                    "agent_id": shard.assigned_agent_id,
                    "total_cases": shard.total_cases,
                    "completed_cases": shard.completed_cases,
                    "passed_cases": shard.passed_cases,
                    "failed_cases": shard.failed_cases,
                    "reassign_count": shard.reassign_count,
                }
                for shard in shards
            ],
        }

    async def _completed_case_ids_for_shard(self, db: AsyncSession, shard: SuiteShard) -> set[int]:
        if not shard.case_ids:
            return set()
        rows = list(
            (
                await db.scalars(
                    select(UIRun.case_id).where(
                        UIRun.case_id.in_(shard.case_ids),
                        UIRun.status.in_(("passed", "failed", "cancelled", "timed_out", "infra_error")),
                    )
                )
            ).all()
        )
        return {int(case_id) for case_id in rows if case_id is not None}

    async def _load_case_tag_maps(
        self, db: AsyncSession, case_ids: list[int]
    ) -> tuple[dict[int, int], dict[int, set[int]], dict[int, int], set[int]]:
        """Return case_limit, case_tags, tag_limit, assigned_cases.

        ``case_limit`` is the strictest max_concurrent across a case's tags (min wins).
        """
        if not case_ids:
            return {}, {}, {}, set()
        assignments = list(
            (
                await db.scalars(
                    select(CaseConcurrencyTagAssignment).where(CaseConcurrencyTagAssignment.case_id.in_(case_ids))
                )
            ).all()
        )
        if not assignments:
            return {}, {}, {}, set()
        tag_ids = {item.tag_id for item in assignments}
        tags = list((await db.scalars(select(CaseConcurrencyTag).where(CaseConcurrencyTag.id.in_(tag_ids)))).all())
        tag_limit = {tag.id: max(1, int(tag.max_concurrent or 1)) for tag in tags}
        case_limit: dict[int, int] = {}
        case_tags: dict[int, set[int]] = {}
        assigned_cases: set[int] = set()
        for item in assignments:
            if item.case_id not in case_ids:
                continue
            limit = tag_limit.get(item.tag_id, 1)
            prev = case_limit.get(item.case_id)
            case_limit[item.case_id] = limit if prev is None else min(prev, limit)
            case_tags.setdefault(item.case_id, set()).add(item.tag_id)
            assigned_cases.add(item.case_id)
        return case_limit, case_tags, tag_limit, assigned_cases

    async def _exclusive_case_ids(self, db: AsyncSession, case_ids: list[int]) -> set[int]:
        """Cases whose strictest tag limit is <= 1 (must not cross shards)."""
        case_limit, _case_tags, _tag_limit, assigned = await self._load_case_tag_maps(db, case_ids)
        return {cid for cid in assigned if case_limit.get(cid, 1) <= 1}

    async def _tagged_case_ids(self, db: AsyncSession, case_ids: list[int]) -> set[int]:
        """Any case that carries at least one concurrency tag."""
        _case_limit, _case_tags, _tag_limit, assigned = await self._load_case_tag_maps(db, case_ids)
        return assigned

    async def _group_by_concurrency_tags(
        self, db: AsyncSession, case_ids: list[int], shard_count: int
    ) -> list[list[int]]:
        """Partition cases honoring each case's strictest max_concurrent.

        Rules:
        - ``case_limit`` = min(max_concurrent) across ALL tags on that case.
        - Cases with ``case_limit <= 1`` that share any exclusive tag (or are alone
          exclusive) stay on ONE shard; exclusive packs never split.
        - Limited tagged cases (case_limit > 1) are packed so that for every tag T,
          the number of shards containing T's cases is ``<= tag.max_concurrent``,
          and no case is placed into more concurrent shards than its own case_limit.
        - Untagged leftovers free-fill remaining capacity; never re-split tagged buckets.
        """
        if not case_ids:
            return []
        case_limit, case_tags, tag_limit, assigned_cases = await self._load_case_tag_maps(db, case_ids)
        if not assigned_cases:
            return self._round_robin(case_ids, shard_count)

        # Union-find exclusive packs: any tag with max_concurrent<=1 binds its cases.
        parent: dict[int, int] = {cid: cid for cid in assigned_cases}

        def _find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def _union(a: int, b: int) -> None:
            ra, rb = _find(a), _find(b)
            if ra != rb:
                parent[rb] = ra

        tag_to_cases: dict[int, list[int]] = {}
        for cid, tags in case_tags.items():
            for tag_id in tags:
                tag_to_cases.setdefault(tag_id, []).append(cid)

        for tag_id, cases in tag_to_cases.items():
            if tag_limit.get(tag_id, 1) <= 1 and len(cases) > 1:
                head = cases[0]
                for other in cases[1:]:
                    _union(head, other)

        exclusive_packs: dict[int, list[int]] = {}
        seen_exclusive: set[int] = set()
        limited_cases: list[int] = []
        for cid in case_ids:
            if cid not in assigned_cases:
                continue
            root = _find(cid)
            pack_mates = [other for other in assigned_cases if _find(other) == root]
            is_exclusive = case_limit.get(cid, 1) <= 1 or (
                len(pack_mates) > 1 and any(case_limit.get(m, 1) <= 1 for m in pack_mates)
            )
            if is_exclusive:
                if cid in seen_exclusive:
                    continue
                pack = [other for other in case_ids if other in assigned_cases and _find(other) == root]
                for other in pack:
                    seen_exclusive.add(other)
                if pack:
                    exclusive_packs[root] = list(dict.fromkeys(pack))
            else:
                limited_cases.append(cid)

        buckets: list[list[int]] = []
        locked_bucket_indexes: set[int] = set()
        for pack in exclusive_packs.values():
            locked_bucket_indexes.add(len(buckets))
            buckets.append(list(pack))

        # tag_id -> set of bucket indexes already holding a case of that tag
        tag_bucket_usage: dict[int, set[int]] = {tag_id: set() for tag_id in tag_limit}
        for idx in locked_bucket_indexes:
            for cid in buckets[idx]:
                for tag_id in case_tags.get(cid, set()):
                    tag_bucket_usage.setdefault(tag_id, set()).add(idx)

        def _can_place(cid: int, bucket_idx: int) -> bool:
            """Check tag concurrency + case_limit if we add cid to bucket_idx (new or existing)."""
            limit = case_limit.get(cid, 1)
            # How many distinct buckets would this case's tags occupy after placement?
            # case_limit bounds how many concurrent shards this case's "cohort" may use
            # via the strictest tag; enforce per-tag max and the case's own min limit.
            for tag_id in case_tags.get(cid, set()):
                used = set(tag_bucket_usage.get(tag_id, set()))
                if bucket_idx not in used:
                    used.add(bucket_idx)
                tag_max = tag_limit.get(tag_id, 1)
                if len(used) > tag_max:
                    return False
                # Strictest case_limit must also cap how many shards this case can join.
                if len(used) > limit:
                    return False
            return True

        def _register(cid: int, bucket_idx: int) -> None:
            for tag_id in case_tags.get(cid, set()):
                tag_bucket_usage.setdefault(tag_id, set()).add(bucket_idx)

        # Place limited cases by strictest case_limit first (harder constraints first).
        for cid in sorted(dict.fromkeys(limited_cases), key=lambda c: (case_limit.get(c, 1), c)):
            placed = False
            # Prefer existing non-locked buckets that already host related tags.
            candidate_indexes = [i for i in range(len(buckets)) if i not in locked_bucket_indexes]

            # Score: buckets that already contain one of this case's tags first.
            def _score(i: int) -> tuple[int, int]:
                overlap = len(case_tags.get(cid, set()) & {t for t, idxs in tag_bucket_usage.items() if i in idxs})
                return (-overlap, i)

            for bucket_idx in sorted(candidate_indexes, key=_score):
                if _can_place(cid, bucket_idx):
                    buckets[bucket_idx].append(cid)
                    _register(cid, bucket_idx)
                    placed = True
                    break
            if placed:
                continue
            # Open a new bucket only if under shard_count and tag limits allow.
            new_idx = len(buckets)
            if new_idx < max(1, int(shard_count)) and _can_place(cid, new_idx):
                buckets.append([cid])
                _register(cid, new_idx)
            else:
                # Fallback: attach to the least-loaded allowed bucket, or force new if empty.
                attached = False
                for bucket_idx in sorted(candidate_indexes, key=lambda i: len(buckets[i])):
                    if _can_place(cid, bucket_idx):
                        buckets[bucket_idx].append(cid)
                        _register(cid, bucket_idx)
                        attached = True
                        break
                if not attached:
                    # Absolute fallback — still respect tag limits by creating a bucket
                    # only when _can_place allows; otherwise co-locate with first non-locked.
                    if _can_place(cid, new_idx):
                        buckets.append([cid])
                        _register(cid, new_idx)
                    elif candidate_indexes:
                        bucket_idx = min(candidate_indexes, key=lambda i: len(buckets[i]))
                        buckets[bucket_idx].append(cid)
                        _register(cid, bucket_idx)
                    else:
                        buckets.append([cid])
                        _register(cid, len(buckets) - 1)

        placed = {cid for bucket in buckets for cid in bucket}
        leftovers = [cid for cid in case_ids if cid not in placed]
        target = max(1, int(shard_count))
        free_slots = max(0, target - len(buckets))
        if leftovers:
            # Free cases only join non-locked buckets or their own free buckets —
            # never re-split / never force into exclusive packs if free slots remain.
            free_bucket_indexes = [i for i in range(len(buckets)) if i not in locked_bucket_indexes]
            if free_slots > 0:
                free_groups = self._round_robin(leftovers, free_slots)
                buckets.extend(free_groups)
            elif free_bucket_indexes:
                for index, case_id in enumerate(leftovers):
                    buckets[free_bucket_indexes[index % len(free_bucket_indexes)]].append(case_id)
            else:
                # Only locked exclusive packs exist and no free slots — append free
                # cases as extra free buckets (better than breaking exclusive packs).
                buckets.extend(self._round_robin(leftovers, max(1, len(leftovers))))

        # Expand ONLY pure free buckets (no tagged cases) to fill target shard_count.
        tagged_set = set(assigned_cases)
        if len(buckets) < target:
            expandable = [
                (idx, bucket)
                for idx, bucket in enumerate(buckets)
                if bucket
                and idx not in locked_bucket_indexes
                and not any(cid in tagged_set for cid in bucket)
                and len(bucket) > 1
            ]
            while len(buckets) < target and expandable:
                idx, bucket = max(expandable, key=lambda item: len(item[1]))
                if len(bucket) <= 1:
                    break
                mid = max(1, len(bucket) // 2)
                left, right = bucket[:mid], bucket[mid:]
                buckets[idx] = left
                buckets.append(right)
                expandable = [
                    (i, b)
                    for i, b in enumerate(buckets)
                    if b and i not in locked_bucket_indexes and not any(cid in tagged_set for cid in b) and len(b) > 1
                ]

        order = {cid: index for index, cid in enumerate(case_ids)}
        normalized = []
        for bucket in buckets:
            unique_bucket = list(dict.fromkeys(bucket))
            unique_bucket.sort(key=lambda cid: order.get(cid, 0))
            if unique_bucket:
                normalized.append(unique_bucket)
        return normalized or [list(case_ids)]

    def _round_robin(self, case_ids: list[int], shard_count: int) -> list[list[int]]:
        buckets = [[] for _ in range(max(1, shard_count))]
        for index, case_id in enumerate(case_ids):
            buckets[index % len(buckets)].append(case_id)
        return [bucket for bucket in buckets if bucket]

    def _greedy_balance(self, case_ids: list[int], durations: dict[int, float], shard_count: int) -> list[list[int]]:
        ordered = sorted(case_ids, key=lambda case_id: durations.get(case_id, 30.0), reverse=True)
        buckets: list[list[int]] = [[] for _ in range(max(1, shard_count))]
        loads = [0.0 for _ in buckets]
        for case_id in ordered:
            index = loads.index(min(loads))
            buckets[index].append(case_id)
            loads[index] += float(durations.get(case_id, 30.0))
        return [bucket for bucket in buckets if bucket]


suite_sharding_service = SuiteShardingService()
