"""UI Automation case management service."""

from __future__ import annotations

import uuid as _uuid
from typing import Any, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.exceptions import NotFoundException, ValidationException
from fastapi_backend.models.ui_automation import UICase, UICaseGroup, UICaseVersion, UIStep
from fastapi_backend.models.workspace import WorkspaceProject
from fastapi_backend.schemas.ui_automation import STEP_TYPES
from fastapi_backend.services import project_service


def _normalize_step_dict(step: dict[str, Any]) -> dict[str, Any]:
    retry = step.get("retry") or {"count": 0, "delay_ms": 0}
    children = step.get("children") or []
    locator = step.get("locator")
    # Persist element repository binding on the locator JSON (UIStep has no element_id column).
    element_id = step.get("element_id")
    if element_id is None and isinstance(locator, dict):
        element_id = locator.get("elementId") if locator.get("elementId") is not None else locator.get("element_id")
    if isinstance(locator, dict) and element_id is not None:
        locator = {**locator, "elementId": int(element_id) if str(element_id).isdigit() else element_id}
    return {
        "id": step.get("id") or str(_uuid.uuid4()),
        "order": step.get("order", 10),
        "name": step.get("name"),
        "type": step["type"],
        "enabled": step.get("enabled", True),
        "breakpoint": step.get("breakpoint", False),
        "locator": locator,
        "input": step.get("input"),
        "timeout_ms": step.get("timeout_ms"),
        "retry": retry,
        "continue_on_failure": step.get("continue_on_failure", False),
        "screenshot": step.get("screenshot", "on-failure"),
        "condition": step.get("condition"),
        "children": children,
    }


async def _validate_group_ownership(
    db: AsyncSession,
    user_id: int,
    group_id: Optional[int],
    *,
    project_id: Optional[int] = None,
) -> None:
    if group_id is None:
        return
    group = await db.get(UICaseGroup, group_id)
    if not group:
        raise ValidationException("Invalid group_id for current user")
    if project_id is not None:
        if group.project_id is not None and int(group.project_id) != int(project_id):
            raise ValidationException("group_id does not belong to active project")
        # 团队项目：成员可引用同项目分组；个人项目：仅本人或 project 匹配
        if group.project_id is None and group.user_id != user_id:
            raise ValidationException("Invalid group_id for current user")
    elif group.user_id != user_id:
        raise ValidationException("Invalid group_id for current user")


async def _validate_parent_group(
    db: AsyncSession,
    user_id: int,
    group_id: int,
    parent_id: Optional[int],
    *,
    project_id: Optional[int] = None,
) -> None:
    if parent_id is None:
        return
    parent = await db.get(UICaseGroup, parent_id)
    if not parent:
        raise ValidationException("Invalid parent_id for current user")
    if project_id is not None:
        if parent.project_id is not None and int(parent.project_id) != int(project_id):
            raise ValidationException("Invalid parent_id for current project")
        if parent.project_id is None and parent.user_id != user_id:
            raise ValidationException("Invalid parent_id for current user")
    elif parent.user_id != user_id:
        raise ValidationException("Invalid parent_id for current user")
    if parent.id == group_id:
        raise ValidationException("A group cannot be its own parent")


async def _validate_project_reference(db: AsyncSession, user_id: int, project_id: Optional[int]) -> int:
    """Validate WorkspaceProject membership; return resolved project id."""
    if project_id is None:
        return await project_service.project_id_for_asset_owner(db, user_id)
    try:
        project = await project_service.require_project_access(
            db, int(user_id), int(project_id), min_role="member"
        )
    except project_service.ProjectNotFoundError as exc:
        raise ValidationException("Invalid project_id") from exc
    except project_service.ProjectAccessError as exc:
        raise ValidationException("No access to project_id") from exc
    return int(project.id)


def _ui_case_project_scope(project_id: int, user_id: int, is_personal: bool):
    if is_personal:
        return or_(
            UICase.project_id == int(project_id),
            and_(UICase.project_id.is_(None), UICase.user_id == int(user_id)),
        )
    return UICase.project_id == int(project_id)


def _validate_step_payload(step: dict[str, Any]) -> None:
    step_type = step.get("type")
    if step_type not in STEP_TYPES:
        raise ValidationException(f"Unsupported step type: {step_type}")


async def list_cases(
    db: AsyncSession,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    group_id: Optional[int] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    project_id: Optional[int] = None,
) -> tuple[list[UICase], int]:
    # 有 project_id：按项目共享；无 project_id：兼容仅本人
    if project_id is not None:
        project = await db.get(WorkspaceProject, int(project_id))
        is_personal = bool(project and project.is_personal)
        query = select(UICase).where(
            UICase.is_active.is_(True),
            _ui_case_project_scope(int(project_id), user_id, is_personal),
        )
    else:
        query = select(UICase).where(UICase.user_id == user_id, UICase.is_active.is_(True))
    if group_id is not None:
        query = query.where(UICase.group_id == group_id)
    if status:
        query = query.where(UICase.status == status)
    if keyword:
        kw = keyword.replace("%", "\\%").replace("_", "\\_")
        query = query.where(UICase.name.like(f"%{kw}%", escape="\\"))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(query.order_by(UICase.updated_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def get_case(
    db: AsyncSession,
    user_id: int,
    case_id: int,
    *,
    project_id: Optional[int] = None,
) -> UICase:
    case = await db.get(UICase, case_id)
    if not case or not case.is_active:
        raise NotFoundException(f"UI case {case_id} not found")
    if project_id is not None:
        project = await db.get(WorkspaceProject, int(project_id))
        is_personal = bool(project and project.is_personal)
        if case.project_id is not None and int(case.project_id) != int(project_id):
            raise NotFoundException(f"UI case {case_id} not found")
        if case.project_id is None:
            # 个人项目可见本人遗留行；团队项目不暴露 NULL
            if not is_personal or int(case.user_id) != int(user_id):
                raise NotFoundException(f"UI case {case_id} not found")
    elif case.user_id != user_id:
        raise NotFoundException(f"UI case {case_id} not found")
    return case


async def create_case(
    db: AsyncSession,
    user_id: int,
    data: dict[str, Any],
    *,
    project_id: Optional[int] = None,
) -> UICase:
    resolved_project_id = await _validate_project_reference(
        db, user_id, project_id if project_id is not None else data.get("project_id")
    )
    await _validate_group_ownership(db, user_id, data.get("group_id"), project_id=resolved_project_id)

    payload = {k: v for k, v in data.items() if v is not None and k not in {"user_id", "owner_id", "project_id"}}
    case = UICase(
        user_id=user_id,
        owner_id=user_id,
        project_id=resolved_project_id,
        **payload,
    )
    db.add(case)
    await db.flush()

    version = await _create_version(
        db,
        case_id=case.id,
        user_id=user_id,
        snapshot={
            "case_id": case.id,
            "name": case.name,
            "description": case.description,
            "base_url": case.base_url,
            "default_timeout_ms": case.default_timeout_ms,
            "navigation_timeout_ms": case.navigation_timeout_ms,
            "viewport": case.viewport,
            "locale": case.locale,
            "timezone_id": case.timezone_id,
            "color_scheme": case.color_scheme,
            "steps": [],
        },
        change_summary="Initial version",
    )
    case.current_version_id = version.id
    await db.flush()
    return case


async def update_case(
    db: AsyncSession,
    user_id: int,
    case_id: int,
    data: dict[str, Any],
    *,
    project_id: Optional[int] = None,
) -> UICase:
    case = await get_case(db, user_id, case_id, project_id=project_id)
    if "group_id" in data:
        await _validate_group_ownership(
            db, user_id, data.get("group_id"), project_id=project_id or case.project_id
        )
    # project_id is controlled by workspace context, not free client reassignment
    data = {k: v for k, v in data.items() if k not in {"project_id", "user_id", "owner_id"}}
    if case.project_id is None and project_id is not None:
        case.project_id = int(project_id)
    for key, value in data.items():
        setattr(case, key, value)
    await db.flush()
    return case


async def delete_case(
    db: AsyncSession,
    user_id: int,
    case_id: int,
    *,
    project_id: Optional[int] = None,
) -> None:
    case = await get_case(db, user_id, case_id, project_id=project_id)
    case.is_active = False
    await db.flush()


async def list_steps(db: AsyncSession, case_id: int) -> list[UIStep]:
    result = await db.execute(select(UIStep).where(UIStep.case_id == case_id).order_by(UIStep.order, UIStep.id))
    return result.scalars().all()


async def batch_save_steps(db: AsyncSession, case_id: int, steps_data: list[dict[str, Any]]) -> list[UIStep]:
    normalized_steps: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw_step in steps_data:
        _validate_step_payload(raw_step)
        step = _normalize_step_dict(raw_step)
        if step["id"] in seen_ids:
            raise ValidationException(f"Duplicate step id: {step['id']}")
        seen_ids.add(step["id"])
        normalized_steps.append(step)

    requested_ids = [step["id"] for step in normalized_steps]
    if requested_ids:
        result = await db.execute(select(UIStep.id).where(UIStep.id.in_(requested_ids), UIStep.case_id != case_id))
        conflicting_ids = set(result.scalars().all())
        for step in normalized_steps:
            if step["id"] in conflicting_ids:
                step["id"] = str(_uuid.uuid4())

    existing = await list_steps(db, case_id)
    for step in existing:
        await db.delete(step)
    await db.flush()

    new_steps: list[UIStep] = []
    for step in normalized_steps:
        row = UIStep(case_id=case_id, **step)
        db.add(row)
        new_steps.append(row)
    await db.flush()
    return new_steps


def step_to_snapshot_dict(step: UIStep) -> dict[str, Any]:
    locator = step.locator
    element_id = None
    if isinstance(locator, dict):
        element_id = locator.get("elementId") if locator.get("elementId") is not None else locator.get("element_id")
        # Ensure desktop engine can read elementId for healing / repo resolution.
        if element_id is not None and "elementId" not in locator:
            locator = {**locator, "elementId": element_id}
    return {
        "id": step.id,
        "order": step.order,
        "name": step.name,
        "type": step.type,
        "enabled": step.enabled,
        "breakpoint": step.breakpoint,
        "locator": locator,
        "element_id": element_id,
        "input": step.input,
        "timeout_ms": step.timeout_ms,
        "retry": step.retry or {"count": 0, "delay_ms": 0},
        "continue_on_failure": step.continue_on_failure,
        "screenshot": step.screenshot or "on-failure",
        "condition": step.condition,
        "children": step.children or [],
    }


async def _create_version(
    db: AsyncSession,
    case_id: int,
    user_id: int,
    snapshot: dict[str, Any],
    change_summary: Optional[str] = None,
) -> UICaseVersion:
    max_ver = (
        await db.execute(select(func.max(UICaseVersion.version_number)).where(UICaseVersion.case_id == case_id))
    ).scalar() or 0
    await db.execute(
        UICaseVersion.__table__.update()
        .where(
            UICaseVersion.case_id == case_id,
            UICaseVersion.is_current.is_(True),
        )
        .values(is_current=False)
    )
    version = UICaseVersion(
        case_id=case_id,
        version_number=max_ver + 1,
        snapshot_json=snapshot,
        change_summary=change_summary,
        created_by=user_id,
        is_current=True,
    )
    db.add(version)
    await db.flush()
    return version


async def create_version_from_case(
    db: AsyncSession, user_id: int, case_id: int, change_summary: Optional[str] = None
) -> UICaseVersion:
    case = await get_case(db, user_id, case_id)
    steps = await list_steps(db, case_id)
    snapshot = {
        "case_id": case.id,
        "name": case.name,
        "description": case.description,
        "base_url": case.base_url,
        "default_timeout_ms": case.default_timeout_ms,
        "navigation_timeout_ms": case.navigation_timeout_ms,
        "viewport": case.viewport,
        "locale": case.locale,
        "timezone_id": case.timezone_id,
        "color_scheme": case.color_scheme,
        "steps": [step_to_snapshot_dict(step) for step in steps],
    }
    version = await _create_version(db, case_id, user_id, snapshot, change_summary)
    case.current_version_id = version.id
    await db.flush()
    return version


async def list_versions(db: AsyncSession, case_id: int, user_id: int) -> list[UICaseVersion]:
    await get_case(db, user_id, case_id)
    result = await db.execute(
        select(UICaseVersion).where(UICaseVersion.case_id == case_id).order_by(UICaseVersion.version_number.desc())
    )
    return result.scalars().all()


async def get_version(db: AsyncSession, case_id: int, version_id: int, user_id: int) -> UICaseVersion:
    await get_case(db, user_id, case_id)
    version = await db.get(UICaseVersion, version_id)
    if not version or version.case_id != case_id:
        raise NotFoundException(f"UI case version {version_id} not found")
    return version


async def restore_version(db: AsyncSession, case_id: int, version_id: int, user_id: int) -> UICase:
    case = await get_case(db, user_id, case_id)
    version = await get_version(db, case_id, version_id, user_id)
    snapshot = version.snapshot_json or {}
    await batch_save_steps(db, case_id, snapshot.get("steps", []))
    for field in [
        "name",
        "description",
        "base_url",
        "default_timeout_ms",
        "navigation_timeout_ms",
        "viewport",
        "locale",
        "timezone_id",
        "color_scheme",
    ]:
        if field in snapshot:
            setattr(case, field, snapshot.get(field))
    restored_version = await create_version_from_case(
        db, user_id, case_id, change_summary=f"Restored from version {version.version_number}"
    )
    case.current_version_id = restored_version.id
    await db.flush()
    return case


async def list_groups(
    db: AsyncSession,
    user_id: int,
    *,
    project_id: Optional[int] = None,
) -> list[UICaseGroup]:
    query = select(UICaseGroup).where(UICaseGroup.user_id == user_id)
    if project_id is not None:
        project = await db.get(WorkspaceProject, int(project_id))
        is_personal = bool(project and project.is_personal)
        if is_personal:
            query = query.where(
                or_(
                    UICaseGroup.project_id == int(project_id),
                    and_(UICaseGroup.project_id.is_(None), UICaseGroup.user_id == int(user_id)),
                )
            )
        else:
            query = query.where(UICaseGroup.project_id == int(project_id))
    result = await db.execute(query.order_by(UICaseGroup.sort_order, UICaseGroup.id))
    return result.scalars().all()


async def create_group(
    db: AsyncSession,
    user_id: int,
    data: dict[str, Any],
    *,
    project_id: Optional[int] = None,
) -> UICaseGroup:
    parent_id = data.get("parent_id")
    if parent_id is not None:
        await _validate_parent_group(db, user_id, 0, parent_id)
    resolved = await _validate_project_reference(
        db, user_id, project_id if project_id is not None else data.get("project_id")
    )
    payload = {k: v for k, v in data.items() if v is not None and k not in {"user_id", "project_id"}}
    group = UICaseGroup(user_id=user_id, project_id=resolved, **payload)
    db.add(group)
    await db.flush()
    return group


async def update_group(
    db: AsyncSession,
    user_id: int,
    group_id: int,
    data: dict[str, Any],
    *,
    project_id: Optional[int] = None,
) -> UICaseGroup:
    group = await db.get(UICaseGroup, group_id)
    if not group or group.user_id != user_id:
        raise NotFoundException(f"UI case group {group_id} not found")
    if project_id is not None and group.project_id is not None and int(group.project_id) != int(project_id):
        raise NotFoundException(f"UI case group {group_id} not found")
    if "parent_id" in data:
        await _validate_parent_group(db, user_id, group_id, data.get("parent_id"))
    data = {k: v for k, v in data.items() if k not in {"project_id", "user_id"}}
    if group.project_id is None and project_id is not None:
        group.project_id = int(project_id)
    for key, value in data.items():
        setattr(group, key, value)
    await db.flush()
    return group


async def delete_group(
    db: AsyncSession,
    user_id: int,
    group_id: int,
    *,
    project_id: Optional[int] = None,
) -> None:
    group = await db.get(UICaseGroup, group_id)
    if not group or group.user_id != user_id:
        raise NotFoundException(f"UI case group {group_id} not found")
    if project_id is not None and group.project_id is not None and int(group.project_id) != int(project_id):
        raise NotFoundException(f"UI case group {group_id} not found")
    await db.delete(group)
    await db.flush()
