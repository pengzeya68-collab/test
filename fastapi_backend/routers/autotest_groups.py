"""
AutoTest 统一路由 - 分组管理（树形层级）

路径前缀: /api/auto-test/groups
映射原 auto_test_platform 的 /api/groups

支持：
- 树形结构返回（含 case_count、sort_order、description）
- 创建/更新/删除分组
- 移动分组（改变 parent_id 与 sort_order），含循环检测
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestGroup,
    AutoTestScenario,
    AutoTestScenarioStep,
)
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    AutoTestGroupCreate,
    AutoTestGroupMove,
    AutoTestGroupUpdate,
)

router = APIRouter(prefix="/api/auto-test/groups", tags=["AutoTest-分组"])


# ========== 工具函数 ==========


def _serialize_group(group: AutoTestGroup) -> Dict[str, Any]:
    """将分组 ORM 对象序列化为字典（含新增字段）"""
    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "description": group.description,
        "sort_order": group.sort_order or 0,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "updated_at": group.updated_at.isoformat() if group.updated_at else None,
    }


async def _detect_cycle(
    db: AsyncSession, group_id: int, new_parent_id: Optional[int], user_id: int
) -> None:
    """循环检测：确保将 group_id 的父设为 new_parent_id 不会形成 A→B→A 环。

    若检测到循环或父分组不存在/不属于当前用户，抛出 HTTPException。
    """
    if new_parent_id is None:
        return
    if new_parent_id == group_id:
        raise HTTPException(status_code=400, detail="不能将分组设为自身的子分组")

    visited = {group_id}
    current_parent_id = new_parent_id
    while current_parent_id is not None:
        if current_parent_id in visited:
            raise HTTPException(
                status_code=400,
                detail="检测到循环引用：目标父分组是当前分组的后代，无法移动",
            )
        visited.add(current_parent_id)
        parent_result = await db.execute(
            select(AutoTestGroup).where(
                AutoTestGroup.id == current_parent_id,
                AutoTestGroup.user_id == user_id,
            )
        )
        parent_group = parent_result.scalar_one_or_none()
        if not parent_group:
            raise HTTPException(status_code=400, detail="父分组不存在或不属于当前用户")
        current_parent_id = parent_group.parent_id


async def _validate_parent_belongs(
    db: AsyncSession, parent_id: Optional[int], user_id: int
) -> None:
    """校验父分组存在且属于当前用户（parent_id 为 None 时跳过）"""
    if parent_id is None:
        return
    result = await db.execute(
        select(AutoTestGroup).where(
            AutoTestGroup.id == parent_id, AutoTestGroup.user_id == user_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="父分组不存在或不属于当前用户")


# ========== 路由端点 ==========


@router.get("/tree")
async def get_group_tree(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有分组，返回树形结构（按 sort_order 排序，含 case_count）"""
    result = await db.execute(
        select(AutoTestGroup)
        .where(AutoTestGroup.user_id == current_user.id)
        .order_by(AutoTestGroup.parent_id, AutoTestGroup.sort_order, AutoTestGroup.id)
    )
    groups = result.scalars().all()

    # 计算每个分组的用例数（只统计当前用户的）
    case_counts: Dict[Optional[int], int] = {}
    count_result = await db.execute(
        select(AutoTestCase.group_id, func.count(AutoTestCase.id))
        .where(AutoTestCase.user_id == current_user.id)
        .group_by(AutoTestCase.group_id)
    )
    for group_id, count in count_result.all():
        case_counts[group_id] = count

    group_dicts = [_serialize_group(g) for g in groups]

    def _build_tree(nodes: List[Dict[str, Any]], parent_id: Optional[int]) -> List[Dict[str, Any]]:
        tree: List[Dict[str, Any]] = []
        for node in nodes:
            if node["parent_id"] == parent_id:
                children = _build_tree(nodes, node["id"])
                node_copy = dict(node)
                node_copy["case_count"] = case_counts.get(node["id"], 0)
                # 始终返回 children 数组（空数组而非 None），便于前端渲染
                node_copy["children"] = children
                tree.append(node_copy)
        return tree

    return _build_tree(group_dicts, None)


@router.get("")
async def get_all_groups(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有分组列表（扁平结构，按 sort_order 排序）"""
    result = await db.execute(
        select(AutoTestGroup)
        .where(AutoTestGroup.user_id == current_user.id)
        .order_by(AutoTestGroup.parent_id, AutoTestGroup.sort_order, AutoTestGroup.name)
    )
    groups = result.scalars().all()
    return [_serialize_group(g) for g in groups]


@router.get("/{group_id}")
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个分组详情"""
    result = await db.execute(
        select(AutoTestGroup).filter(
            AutoTestGroup.id == group_id, AutoTestGroup.user_id == current_user.id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return _serialize_group(group)


@router.post("", status_code=201)
async def create_group(
    group_in: AutoTestGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新分组"""
    await _validate_parent_belongs(db, group_in.parent_id, current_user.id)

    group = AutoTestGroup(**group_in.model_dump(), user_id=current_user.id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return _serialize_group(group)


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    group_in: AutoTestGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分组（含移动到新父分组，带循环检测）"""
    result = await db.execute(
        select(AutoTestGroup).filter(
            AutoTestGroup.id == group_id, AutoTestGroup.user_id == current_user.id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    update_data = group_in.model_dump(exclude_unset=True)
    new_parent_id = update_data.get("parent_id", group.parent_id)

    # 若 parent_id 变更，则进行循环检测与归属校验
    if "parent_id" in update_data:
        await _detect_cycle(db, group_id, new_parent_id, current_user.id)
        await _validate_parent_belongs(db, new_parent_id, current_user.id)

    for field, value in update_data.items():
        if field in ("id", "user_id", "created_at"):
            continue
        setattr(group, field, value)

    await db.commit()
    await db.refresh(group)
    return _serialize_group(group)


@router.put("/{group_id}/move")
async def move_group(
    group_id: int,
    move_in: AutoTestGroupMove,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """移动分组：改变 parent_id 和/或 sort_order（带循环检测）"""
    result = await db.execute(
        select(AutoTestGroup).filter(
            AutoTestGroup.id == group_id, AutoTestGroup.user_id == current_user.id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    move_data = move_in.model_dump(exclude_unset=True)
    if not move_data:
        raise HTTPException(status_code=400, detail="未提供任何移动字段")

    new_parent_id = move_data.get("parent_id", group.parent_id)
    if "parent_id" in move_data:
        await _detect_cycle(db, group_id, new_parent_id, current_user.id)
        await _validate_parent_belongs(db, new_parent_id, current_user.id)
        group.parent_id = new_parent_id

    if "sort_order" in move_data:
        group.sort_order = move_data["sort_order"]

    await db.commit()
    await db.refresh(group)
    return _serialize_group(group)


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    move_cases_to_parent: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分组。

    - 子分组处理：若有子分组则拒绝删除（需先删除子分组）。
    - 用例处理：
      * move_cases_to_parent=True 且存在父分组：将用例移动到父分组。
      * 否则：解除场景步骤引用并删除分组下用例。
    """
    result = await db.execute(
        select(AutoTestGroup).filter(
            AutoTestGroup.id == group_id, AutoTestGroup.user_id == current_user.id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 检查是否有子分组
    child_result = await db.execute(
        select(AutoTestGroup).filter(
            AutoTestGroup.parent_id == group_id,
            AutoTestGroup.user_id == current_user.id,
        )
    )
    children = child_result.scalars().all()
    if children:
        raise HTTPException(
            status_code=400,
            detail=f"请先删除子分组（共 {len(children)} 个）",
        )

    # 查找分组下所有用例
    cases_result = await db.execute(
        select(AutoTestCase).filter(
            AutoTestCase.group_id == group_id,
            AutoTestCase.user_id == current_user.id,
        )
    )
    cases = cases_result.scalars().all()

    moved_count = 0
    deleted_count = 0
    if cases:
        # 决定用例去向：移动到父分组（若启用且父分组存在），否则删除
        should_move = move_cases_to_parent and group.parent_id is not None
        if should_move:
            for case in cases:
                case.group_id = group.parent_id
            moved_count = len(cases)
        else:
            case_ids = [case.id for case in cases]
            # 将引用这些用例的当前用户的场景步骤 api_case_id 置空，避免悬挂引用
            steps_result = await db.execute(
                select(AutoTestScenarioStep)
                .join(
                    AutoTestScenario,
                    AutoTestScenarioStep.scenario_id == AutoTestScenario.id,
                )
                .where(
                    AutoTestScenarioStep.api_case_id.in_(case_ids),
                    AutoTestScenario.user_id == current_user.id,
                )
            )
            for step in steps_result.scalars().all():
                step.api_case_id = None
            for case in cases:
                await db.delete(case)
            deleted_count = len(cases)

    await db.delete(group)
    await db.commit()

    detail_parts = [f"删除成功"]
    if moved_count:
        detail_parts.append(f"移动 {moved_count} 个用例到父分组")
    if deleted_count:
        detail_parts.append(f"删除 {deleted_count} 个用例")
    return {"success": True, "message": "，".join(detail_parts)}
