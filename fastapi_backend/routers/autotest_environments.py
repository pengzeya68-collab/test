"""
AutoTest 统一路由 - 环境管理

路径前缀: /api/auto-test/environments
映射原 auto_test_platform 的 /api/environments
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestEnvironment
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import AutoTestEnvironmentCreate
from fastapi_backend.schemas.environments import EnvironmentUpdate

router = APIRouter(prefix="/api/auto-test/environments", tags=["AutoTest-环境"])

import re

_SENSITIVE_PATTERN = re.compile(r"(password|secret|key|token)", re.IGNORECASE)


def _mask_variables(variables):
    """对敏感 key 的值做脱敏处理"""
    if not isinstance(variables, dict):
        return variables
    return {k: "****" if _SENSITIVE_PATTERN.search(k) else v for k, v in variables.items()}


def _env_to_dict(env):
    """将环境对象转为字典"""
    return {
        "id": env.id,
        "name": env.env_name,
        "env_name": env.env_name,
        "base_url": env.base_url,
        "variables": _mask_variables(env.variables),
        "is_default": env.is_default,
        "created_at": env.created_at.isoformat() if env.created_at else None,
    }


@router.get("")
async def get_all_environments(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有环境"""
    result = await db.execute(
        select(AutoTestEnvironment)
        .where(AutoTestEnvironment.user_id == current_user.id)
        .order_by(AutoTestEnvironment.created_at)
    )
    envs = result.scalars().all()
    return [_env_to_dict(e) for e in envs]


@router.get("/{env_id}")
async def get_environment(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个环境"""
    result = await db.execute(
        select(AutoTestEnvironment).filter(
            AutoTestEnvironment.id == env_id, AutoTestEnvironment.user_id == current_user.id
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    return _env_to_dict(env)


@router.post("", status_code=201)
async def create_environment(
    env_in: AutoTestEnvironmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建环境"""
    data = env_in.model_dump()
    if "name" in data:
        data["env_name"] = data.pop("name")

    if data.get("is_default"):
        await db.execute(
            update(AutoTestEnvironment).where(AutoTestEnvironment.user_id == current_user.id).values(is_default=False)
        )

    data["user_id"] = current_user.id
    env = AutoTestEnvironment(**data)
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return _env_to_dict(env)


@router.put("/{env_id}")
async def update_environment(
    env_id: int,
    env_in: EnvironmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新环境"""
    result = await db.execute(
        select(AutoTestEnvironment).filter(
            AutoTestEnvironment.id == env_id, AutoTestEnvironment.user_id == current_user.id
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    _set_fields = env_in.model_dump(exclude_unset=True)
    if _set_fields.get("is_default"):
        await db.execute(
            update(AutoTestEnvironment)
            .where(AutoTestEnvironment.user_id == current_user.id, AutoTestEnvironment.id != env_id)
            .values(is_default=False)
        )

    for field, value in _set_fields.items():
        if field == "name":
            field = "env_name"
        if field == "variables" and isinstance(value, dict):
            existing_vars = env.variables if isinstance(env.variables, dict) else {}
            merged = dict(existing_vars)
            for k, v in value.items():
                if v == "****":
                    continue
                merged[k] = v
            value = merged
        setattr(env, field, value)

    await db.commit()
    await db.refresh(env)
    return _env_to_dict(env)


@router.delete("/{env_id}")
async def delete_environment(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除环境"""
    result = await db.execute(
        select(AutoTestEnvironment).filter(
            AutoTestEnvironment.id == env_id, AutoTestEnvironment.user_id == current_user.id
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    await db.delete(env)
    await db.commit()
    return {"success": True, "message": "删除成功"}
