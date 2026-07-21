"""UI automation suite management and immutable execution plans."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_backend.core.exceptions import NotFoundException, ValidationException
from fastapi_backend.models.ui_automation import UISuite, UISuiteItem
from fastapi_backend.services.ui_automation import case_service


async def get_suite(db: AsyncSession, user_id: int, suite_id: int, *, with_items: bool = True) -> UISuite:
    query = (
        select(UISuite)
        .where(UISuite.id == suite_id, UISuite.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    if with_items:
        query = query.options(selectinload(UISuite.items))
    suite = (await db.execute(query)).scalar_one_or_none()
    if not suite:
        raise NotFoundException(f"UI suite {suite_id} not found")
    return suite


async def list_suites(db: AsyncSession, user_id: int) -> list[UISuite]:
    result = await db.execute(
        select(UISuite)
        .options(selectinload(UISuite.items))
        .where(UISuite.user_id == user_id)
        .order_by(UISuite.updated_at.desc(), UISuite.id.desc())
    )
    return result.scalars().unique().all()


async def create_suite(db: AsyncSession, user_id: int, payload: dict[str, Any]) -> UISuite:
    suite = UISuite(user_id=user_id, **payload)
    db.add(suite)
    await db.flush()
    return await get_suite(db, user_id, suite.id)


async def update_suite(db: AsyncSession, user_id: int, suite_id: int, payload: dict[str, Any]) -> UISuite:
    suite = await get_suite(db, user_id, suite_id)
    for key, value in payload.items():
        setattr(suite, key, value)
    await db.flush()
    return suite


async def delete_suite(db: AsyncSession, user_id: int, suite_id: int) -> None:
    suite = await get_suite(db, user_id, suite_id)
    await db.delete(suite)
    await db.flush()


async def replace_items(db: AsyncSession, user_id: int, suite_id: int, items: list[dict[str, Any]]) -> UISuite:
    suite = await get_suite(db, user_id, suite_id)
    case_ids = [item["case_id"] for item in items]
    if len(case_ids) != len(set(case_ids)):
        raise ValidationException("A case can only appear once in a suite")

    validated: list[dict[str, Any]] = []
    for position, item in enumerate(items):
        case = await case_service.get_case(db, user_id, item["case_id"])
        pinned = item.get("pinned_version_id")
        if pinned is not None:
            await case_service.get_version(db, case.id, pinned, user_id)
        data_source = item.get("data_source")
        if data_source is not None:
            rows = data_source.get("rows")
            if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
                raise ValidationException("Suite data_source.rows must be a non-empty list of objects")
            if len(rows) > 1000:
                raise ValidationException("Suite data source cannot exceed 1000 rows")
        validated.append({**item, "order": item.get("order") or (position + 1) * 10})

    for current in list(suite.items):
        await db.delete(current)
    await db.flush()
    for item in validated:
        db.add(UISuiteItem(suite_id=suite.id, **item))
    await db.flush()
    return await get_suite(db, user_id, suite.id)


async def build_execution_plan(db: AsyncSession, user_id: int, suite_id: int) -> dict[str, Any]:
    suite = await get_suite(db, user_id, suite_id)
    entries: list[dict[str, Any]] = []
    for item in sorted((value for value in suite.items if value.enabled), key=lambda value: value.order):
        case = await case_service.get_case(db, user_id, item.case_id)
        version_id = item.pinned_version_id or case.current_version_id
        if not version_id:
            raise ValidationException(f"Case {case.name} has no saved version")
        version = await case_service.get_version(db, case.id, version_id, user_id)
        snapshot = dict(version.snapshot_json or {})
        rows = (item.data_source or {}).get("rows") or [{}]
        overrides = dict(item.overrides or {})
        for iteration, row in enumerate(rows):
            variables = {**overrides, **row}
            entries.append(
                {
                    "suite_item_id": item.id,
                    "case_id": case.id,
                    "case_name": case.name,
                    "case_version_id": version.id,
                    "iteration": iteration,
                    "variables": {key: "" if value is None else str(value) for key, value in variables.items()},
                    "snapshot": snapshot,
                }
            )
    if not entries:
        raise ValidationException("Suite has no enabled executable cases")
    return {
        "suite_id": suite.id,
        "suite_name": suite.name,
        "stop_on_first_failure": suite.stop_on_first_failure,
        "entries": entries,
    }
