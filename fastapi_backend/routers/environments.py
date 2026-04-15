"""
测试环境路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import Environment
from fastapi_backend.schemas.environments import (
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentResponse,
)

router = APIRouter(prefix="/api/v1/environments", tags=["测试环境"])


@router.get("/", response_model=List[EnvironmentResponse])
async def get_all_environments(db: AsyncSession = Depends(get_db)):
    """获取所有环境"""
    result = await db.execute(select(Environment).order_by(Environment.created_at))
    envs = result.scalars().all()
    return envs


@router.get("/{env_id}", response_model=EnvironmentResponse)
async def get_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个环境"""
    result = await db.execute(select(Environment).filter(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    return env


@router.post("/", response_model=EnvironmentResponse, status_code=201)
async def create_environment(
    env_in: EnvironmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建环境"""
    env = Environment(**env_in.model_dump())
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return env


@router.put("/{env_id}", response_model=EnvironmentResponse)
async def update_environment(
    env_id: int,
    env_in: EnvironmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新环境"""
    result = await db.execute(select(Environment).filter(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    # 如果设置为默认，取消其他默认
    if env_in.is_default:
        await db.execute(update(Environment).where(Environment.id != env_id).values(is_default=False))

    for field, value in env_in.model_dump(exclude_unset=True).items():
        setattr(env, field, value)

    await db.commit()
    await db.refresh(env)
    return env


@router.delete("/{env_id}")
async def delete_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    """删除环境"""
    result = await db.execute(select(Environment).filter(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    await db.delete(env)
    await db.commit()
    return {"success": True, "message": "删除成功"}
