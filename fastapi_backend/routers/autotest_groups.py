"""
AutoTest 统一路由 - 分组管理

路径前缀: /api/auto-test/groups
映射原 auto_test_platform 的 /api/groups
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestGroup, AutoTestCase, AutoTestScenario, AutoTestScenarioStep
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    AutoTestGroupCreate,
    AutoTestGroupUpdate,
)

router = APIRouter(prefix="/api/auto-test/groups", tags=["AutoTest-分组"])


@router.get("/tree")
async def get_group_tree(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有分组，返回树形结构"""
    result = await db.execute(
        select(AutoTestGroup)
        .where(AutoTestGroup.user_id == current_user.id)
        .order_by(AutoTestGroup.parent_id, AutoTestGroup.id)
    )
    groups = result.scalars().all()

    # 计算每个分组的用例数（只统计当前用户的）
    case_counts = {}
    count_result = await db.execute(
        select(AutoTestCase.group_id, func.count(AutoTestCase.id))
        .where(AutoTestCase.user_id == current_user.id)
        .group_by(AutoTestCase.group_id)
    )
    for group_id, count in count_result.all():
        case_counts[group_id] = count

    # 构建字典列表
    group_dicts = [
        {
            "id": g.id,
            "name": g.name,
            "parent_id": g.parent_id,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in groups
    ]

    def _build_tree(nodes, parent_id=None):
        tree = []
        for node in nodes:
            if node["parent_id"] == parent_id:
                children = _build_tree(nodes, node["id"])
                node_copy = dict(node)
                node_copy["case_count"] = case_counts.get(node["id"], 0)
                node_copy["children"] = children
                tree.append(node_copy)
        return tree

    return _build_tree(group_dicts)


@router.get("")
async def get_all_groups(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有分组列表（扁平结构）"""
    result = await db.execute(
        select(AutoTestGroup)
        .where(AutoTestGroup.user_id == current_user.id)
        .order_by(AutoTestGroup.name)
    )
    groups = result.scalars().all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "parent_id": g.parent_id,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in groups
    ]


@router.get("/{group_id}")
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个分组详情"""
    result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.id == group_id, AutoTestGroup.user_id == current_user.id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.post("", status_code=201)
async def create_group(
    group_in: AutoTestGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新分组"""
    # 校验 parent_id 归属当前用户
    if group_in.parent_id is not None:
        parent_result = await db.execute(
            select(AutoTestGroup).where(AutoTestGroup.id == group_in.parent_id, AutoTestGroup.user_id == current_user.id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="父分组不存在或不属于当前用户")

    group = AutoTestGroup(**group_in.model_dump(), user_id=current_user.id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    group_in: AutoTestGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分组"""
    result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.id == group_id, AutoTestGroup.user_id == current_user.id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    for field, value in group_in.model_dump(exclude_unset=True).items():
        if field in ("id", "user_id", "created_at"):
            continue
        setattr(group, field, value)

    # 循环引用检测：如果修改了 parent_id，检查 parent 链是否会形成环
    if group.parent_id is not None:
        visited = {group.id}
        current_parent_id = group.parent_id
        while current_parent_id is not None:
            if current_parent_id in visited:
                raise HTTPException(status_code=400, detail="不能设置循环引用的父分组")
            visited.add(current_parent_id)
            parent_result = await db.execute(
                select(AutoTestGroup).where(
                    AutoTestGroup.id == current_parent_id,
                    AutoTestGroup.user_id == current_user.id
                )
            )
            parent_group = parent_result.scalar_one_or_none()
            if not parent_group:
                raise HTTPException(status_code=400, detail="父分组不存在或不属于当前用户")
            current_parent_id = parent_group.parent_id

    await db.commit()
    await db.refresh(group)
    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分组（级联删除分组下的用例，并解除场景步骤引用）"""
    result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.id == group_id, AutoTestGroup.user_id == current_user.id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 检查是否有子分组
    child_result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.parent_id == group_id, AutoTestGroup.user_id == current_user.id))
    children = child_result.scalars().all()
    if children:
        raise HTTPException(status_code=400, detail="请先删除子分组")

    # 查找分组下所有用例
    cases_result = await db.execute(select(AutoTestCase).filter(AutoTestCase.group_id == group_id, AutoTestCase.user_id == current_user.id))
    cases = cases_result.scalars().all()

    if cases:
        case_ids = [case.id for case in cases]
        # 删除引用这些用例的场景步骤（包括其他用户场景中的引用，避免悬挂引用）
        steps_result = await db.execute(
            select(AutoTestScenarioStep)
            .where(AutoTestScenarioStep.api_case_id.in_(case_ids))
        )
        for step in steps_result.scalars().all():
            await db.delete(step)
        # 删除用例
        for case in cases:
            await db.delete(case)

    await db.delete(group)
    await db.commit()
    return {"success": True, "message": f"删除成功，同时删除了 {len(cases)} 个用例"}
