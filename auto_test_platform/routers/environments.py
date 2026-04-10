"""
环境管理路由
提供环境的增删改查接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from auto_test_platform.database import get_session
from auto_test_platform.models import Environment
from auto_test_platform.schemas import EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse

router = APIRouter(prefix="/environments", tags=["环境管理"])


@router.get("", response_model=List[EnvironmentResponse])
async def get_environments(session: AsyncSession = Depends(get_session)):
    """
    获取所有环境列表
    """
    result = await session.execute(select(Environment).order_by(Environment.id))
    environments = result.scalars().all()
    return environments


@router.post("", response_model=EnvironmentResponse)
async def create_environment(
    env: EnvironmentCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    创建新环境

    - env_name: 环境名称（必填，如：测试环境、预生产环境）
    - base_url: 基础路径（可选，如：https://api.example.com）
    - variables: 全局变量（JSON格式，可用于存储 api_prefix、token 等）
    - is_default: 是否为默认环境（可选，默认 False）
    """
    # 如果设置为默认环境，先取消其他默认
    if env.is_default:
        await session.execute(
            update(Environment).where(Environment.is_default == True).values(is_default=False)
        )

    db_env = Environment(**env.model_dump())
    session.add(db_env)
    await session.commit()
    await session.refresh(db_env)
    return db_env


@router.get("/{env_id}", response_model=EnvironmentResponse)
async def get_environment(env_id: int, session: AsyncSession = Depends(get_session)):
    """
    获取指定环境详情
    """
    result = await session.execute(
        select(Environment).where(Environment.id == env_id)
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    return env


@router.put("/{env_id}", response_model=EnvironmentResponse)
async def update_environment(
    env_id: int,
    env_update: EnvironmentUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    更新环境信息
    """
    result = await session.execute(
        select(Environment).where(Environment.id == env_id)
    )
    db_env = result.scalar_one_or_none()
    if not db_env:
        raise HTTPException(status_code=404, detail="环境不存在")

    # 如果设置为默认环境，先取消其他默认
    if env_update.is_default:
        await session.execute(
            update(Environment).where(Environment.is_default == True).values(is_default=False)
        )

    update_data = env_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_env, key, value)

    await session.commit()
    await session.refresh(db_env)
    return db_env


@router.delete("/{env_id}", status_code=204)
async def delete_environment(env_id: int, session: AsyncSession = Depends(get_session)):
    """
    删除环境
    """
    result = await session.execute(
        select(Environment).where(Environment.id == env_id)
    )
    db_env = result.scalar_one_or_none()
    if not db_env:
        raise HTTPException(status_code=404, detail="环境不存在")

    await session.delete(db_env)
    await session.commit()
    return None
