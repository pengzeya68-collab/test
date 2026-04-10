"""
接口分组路由
- 获取树形结构
- 增删改查
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import ApiGroup
from fastapi_backend.schemas.groups import (
    ApiGroupCreate,
    ApiGroupUpdate,
    ApiGroupResponse,
    ApiGroupTreeNode,
)

router = APIRouter(prefix="/api/groups", tags=["接口分组"])


def build_tree(nodes, parent_id=None):
    """递归构建树形结构"""
    tree = []
    for node in nodes:
        if node.parent_id == parent_id:
            children = build_tree(nodes, node.id)
            tree_node = {
                "id": node.id,
                "name": node.name,
                "description": node.description,
                "parent_id": node.parent_id,
                "created_at": node.created_at,
                "updated_at": node.updated_at,
                "case_count": 0,
                "children": children
            }
            tree.append(tree_node)
    return tree


@router.get("/tree", response_model=List[ApiGroupTreeNode])
async def get_group_tree(db: AsyncSession = Depends(get_db)):
    """获取所有分组，返回树形结构"""
    result = await db.execute(select(ApiGroup).order_by(ApiGroup.parent_id, ApiGroup.id))
    groups = result.scalars().all()

    tree = build_tree(groups)
    return tree


@router.get("/", response_model=List[ApiGroupResponse])
async def get_all_groups(db: AsyncSession = Depends(get_db)):
    """获取所有分组列表（扁平结构）"""
    result = await db.execute(select(ApiGroup).order_by(ApiGroup.name))
    groups = result.scalars().all()
    return groups


@router.get("/{group_id}", response_model=ApiGroupResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个分组详情"""
    result = await db.execute(select(ApiGroup).filter(ApiGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


@router.post("/", response_model=ApiGroupResponse, status_code=201)
async def create_group(group_in: ApiGroupCreate, db: AsyncSession = Depends(get_db)):
    """创建新分组"""
    group = ApiGroup(**group_in.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.put("/{group_id}", response_model=ApiGroupResponse)
async def update_group(
    group_id: int,
    group_in: ApiGroupUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新分组"""
    result = await db.execute(select(ApiGroup).filter(ApiGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    for field, value in group_in.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """删除分组"""
    result = await db.execute(select(ApiGroup).filter(ApiGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 检查是否有子分组
    child_result = await db.execute(select(ApiGroup).filter(ApiGroup.parent_id == group_id))
    children = child_result.scalars().all()
    if children:
        raise HTTPException(status_code=400, detail="请先删除子分组")

    await db.delete(group)
    await db.commit()
    return {"success": True, "message": "删除成功"}
