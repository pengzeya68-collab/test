"""
AutoTest 统一路由 - 环境管理

路径前缀: /api/auto-test/environments
映射原 auto_test_platform 的 /api/environments
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestEnvironment
from fastapi_backend.schemas.autotest import (
    AutoTestEnvironmentCreate,
    AutoTestEnvironmentUpdate,
)

router = APIRouter(prefix="/api/auto-test/environments", tags=["AutoTest-环境"], dependencies=[Depends(get_current_user)])


def _env_to_dict(env):
    """将环境对象转为字典"""
    return {
        "id": env.id,
        "name": env.env_name,
        "env_name": env.env_name,
        "base_url": env.base_url,
        "variables": env.variables,
        "is_default": env.is_default,
        "created_at": env.created_at.isoformat() if env.created_at else None,
    }


@router.get("/")
async def get_all_environments(db: AsyncSession = Depends(get_db)):
    """获取所有环境"""
    result = await db.execute(select(AutoTestEnvironment).order_by(AutoTestEnvironment.created_at))
    envs = result.scalars().all()
    return [_env_to_dict(e) for e in envs]


@router.get("/{env_id}")
async def get_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个环境"""
    result = await db.execute(select(AutoTestEnvironment).filter(AutoTestEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    return _env_to_dict(env)


@router.post("/", status_code=201)
async def create_environment(
    env_in: AutoTestEnvironmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建环境"""
    env = AutoTestEnvironment(**env_in.model_dump())
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return _env_to_dict(env)


@router.put("/{env_id}")
async def update_environment(
    env_id: int,
    env_in: AutoTestEnvironmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新环境"""
    result = await db.execute(select(AutoTestEnvironment).filter(AutoTestEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    if env_in.is_default:
        await db.execute(
            update(AutoTestEnvironment)
            .where(AutoTestEnvironment.id != env_id)
            .values(is_default=False)
        )

    for field, value in env_in.model_dump(exclude_unset=True).items():
        setattr(env, field, value)

    await db.commit()
    await db.refresh(env)
    return _env_to_dict(env)


@router.delete("/{env_id}")
async def delete_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    """删除环境"""
    result = await db.execute(select(AutoTestEnvironment).filter(AutoTestEnvironment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    await db.delete(env)
    await db.commit()
    return {"success": True, "message": "删除成功"}
