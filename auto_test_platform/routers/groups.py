"""
分组管理路由
提供树状分组的增删改查接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from auto_test_platform.database import get_session
from auto_test_platform.models import ApiGroup, ApiCase
from auto_test_platform.schemas import ApiGroupCreate, ApiGroupUpdate, ApiGroupResponse, ApiGroupTree

router = APIRouter(prefix="/groups", tags=["分组管理"])


@router.get("", response_model=List[ApiGroupTree])
async def get_groups(session: AsyncSession = Depends(get_session)):
    """
    获取所有分组（树状结构）

    返回包含子分组的树状列表，每个节点包含 case_count 表示该分组下的用例数量
    """
    # 查询所有分组
    result = await session.execute(select(ApiGroup).order_by(ApiGroup.id))
    groups = result.scalars().all()

    # 查询每个分组的用例数量
    case_count_result = await session.execute(
        select(ApiGroup.id, func.count(ApiCase.id).label("case_count"))
        .outerjoin(ApiCase, ApiGroup.id == ApiCase.group_id)
        .group_by(ApiGroup.id)
    )
    case_count_map = {row.id: row.case_count for row in case_count_result.all()}

    # 构建树状结构
    def build_tree(parent_id=None):
        return [
            {
                "id": g.id,
                "name": g.name,
                "parent_id": g.parent_id,
                "created_at": g.created_at,
                "case_count": case_count_map.get(g.id, 0),
                "children": build_tree(g.id)
            }
            for g in groups if g.parent_id == parent_id
        ]

    return build_tree()


@router.post("", response_model=ApiGroupResponse)
async def create_group(group: ApiGroupCreate, session: AsyncSession = Depends(get_session)):
    """
    创建新分组

    - name: 分组名称（必填）
    - parent_id: 父级分组ID（可选，用于创建子分组）
    """
    # 验证父分组存在（如果指定了 parent_id）
    if group.parent_id:
        result = await session.execute(
            select(ApiGroup).where(ApiGroup.id == group.parent_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="父级分组不存在")

    db_group = ApiGroup(**group.model_dump())
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    return db_group


@router.get("/{group_id}", response_model=ApiGroupResponse)
async def get_group(group_id: int, session: AsyncSession = Depends(get_session)):
    """
    获取指定分组详情
    """
    result = await session.execute(
        select(ApiGroup).where(ApiGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


@router.put("/{group_id}", response_model=ApiGroupResponse)
async def update_group(
    group_id: int,
    group_update: ApiGroupUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    更新分组信息
    """
    result = await session.execute(
        select(ApiGroup).where(ApiGroup.id == group_id)
    )
    db_group = result.scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 验证父分组（如果指定了新的 parent_id）
    if group_update.parent_id is not None:
        if group_update.parent_id == group_id:
            raise HTTPException(status_code=400, detail="不能将自己设为父分组")
        if group_update.parent_id:
            result = await session.execute(
                select(ApiGroup).where(ApiGroup.id == group_update.parent_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="父级分组不存在")

    update_data = group_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_group, key, value)

    await session.commit()
    await session.refresh(db_group)
    return db_group


@router.delete("/{group_id}", status_code=204)
async def delete_group(group_id: int, session: AsyncSession = Depends(get_session)):
    """
    删除分组

    注意：如果分组下有用例或子分组，会导致删除失败
    """
    result = await session.execute(
        select(ApiGroup).where(ApiGroup.id == group_id)
    )
    db_group = result.scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="分组不存在")

    await session.delete(db_group)
    await session.commit()
    return None