"""
AutoTest 统一路由 - 分组管理

路径前缀: /api/auto-test/groups
映射原 auto_test_platform 的 /api/groups
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestGroup, AutoTestCase
from fastapi_backend.schemas.autotest import (
    AutoTestGroupCreate,
    AutoTestGroupUpdate,
)

router = APIRouter(prefix="/api/auto-test/groups", tags=["AutoTest-分组"], dependencies=[Depends(get_current_user)])


@router.get("/tree")
async def get_group_tree(db: AsyncSession = Depends(get_db)):
    """获取所有分组，返回树形结构"""
    result = await db.execute(select(AutoTestGroup).order_by(AutoTestGroup.parent_id, AutoTestGroup.id))
    groups = result.scalars().all()

    # 计算每个分组的用例数
    case_counts = {}
    count_result = await db.execute(
        select(AutoTestCase.group_id, func.count(AutoTestCase.id)).group_by(AutoTestCase.group_id)
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


@router.get("/")
async def get_all_groups(db: AsyncSession = Depends(get_db)):
    """获取所有分组列表（扁平结构）"""
    result = await db.execute(select(AutoTestGroup).order_by(AutoTestGroup.name))
    groups = result.scalars().all()
    # 不用严格 response_model 验证，因为数据库中 parent_id 可能为非整数
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
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个分组详情"""
    result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.post("/", status_code=201)
async def create_group(group_in: AutoTestGroupCreate, db: AsyncSession = Depends(get_db)):
    """创建新分组"""
    group = AutoTestGroup(**group_in.model_dump())
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
    db: AsyncSession = Depends(get_db),
):
    """更新分组"""
    result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    for field, value in group_in.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    await db.commit()
    await db.refresh(group)
    return {
        "id": group.id,
        "name": group.name,
        "parent_id": group.parent_id,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """删除分组"""
    result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 检查是否有子分组
    child_result = await db.execute(select(AutoTestGroup).filter(AutoTestGroup.parent_id == group_id))
    children = child_result.scalars().all()
    if children:
        raise HTTPException(status_code=400, detail="请先删除子分组")

    await db.delete(group)
    await db.commit()
    return {"success": True, "message": "删除成功"}
