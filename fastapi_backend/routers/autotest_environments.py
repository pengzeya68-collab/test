"""
AutoTest 统一路由 - 环境管理

路径前缀: /api/auto-test/environments
映射原 auto_test_platform 的 /api/environments
"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.core.exceptions import BusinessException
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.deps.project_context import (
    get_active_project_id,
    get_active_project_id_member,
    is_personal_project,
    project_scope_with_legacy_null,
)
from fastapi_backend.models.autotest import AutoTestEnvironment
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import AutoTestEnvironmentCreate, AutoTestEnvironmentUpdate
from fastapi_backend.services.autotest_variable_service import (
    EnvironmentNotFoundError,
    InheritanceError,
    get_effective_variables,
    get_inheritance_chain,
    validate_parent_id,
)

router = APIRouter(prefix="/api/auto-test/environments", tags=["AutoTest-环境"])


_SENSITIVE_PATTERN = re.compile(r"(password|secret|key|token)", re.IGNORECASE)


def _mask_variables(variables):
    """对敏感 key 的值做脱敏处理"""
    if not isinstance(variables, dict):
        return variables
    return {k: "****" if _SENSITIVE_PATTERN.search(k) else v for k, v in variables.items()}


def _env_to_dict(env):
    """将环境对象转为字典（要求 env.parent 已被 eager load，避免 async lazy load 报错）"""
    # 仅当 parent 关系已加载时才取名称，避免触发异步懒加载
    parent_name = None
    try:
        parent = env.parent  # noqa: B018
        if parent is not None:
            parent_name = parent.env_name
    except Exception:
        # 关系未加载（异步上下文），忽略，返回 None
        parent_name = None
    return {
        "id": env.id,
        "name": env.env_name,
        "env_name": env.env_name,
        "base_url": env.base_url,
        "variables": _mask_variables(env.variables),
        "is_default": env.is_default,
        "parent_id": env.parent_id,
        "parent_name": parent_name,
        "project_id": getattr(env, "project_id", None),
        "created_at": env.created_at.isoformat() if env.created_at else None,
    }


async def _env_scope(db: AsyncSession, user_id: int, project_id: int):
    personal = await is_personal_project(db, project_id)
    return project_scope_with_legacy_null(
        AutoTestEnvironment.project_id,
        project_id,
        user_id_column=AutoTestEnvironment.user_id,
        user_id=user_id,
        is_personal_active=personal,
    )


def _raise_inheritance_error(exc: InheritanceError) -> None:
    """将继承异常映射为 BusinessException（携带结构化 code）"""
    if isinstance(exc, EnvironmentNotFoundError):
        raise BusinessException(detail=exc.message, code=exc.code, status_code=404)
    # 循环继承 / 超出深度 / 其他继承错误统一 400
    raise BusinessException(detail=exc.message, code=exc.code, status_code=400)


async def _load_env_with_parent(
    db: AsyncSession,
    env_id: int,
    user_id: int,
    *,
    project_id: int | None = None,
) -> Optional[AutoTestEnvironment]:
    """按 id + 项目可见范围加载环境并 eager load parent 关系（成员共享）"""
    filters = [AutoTestEnvironment.id == env_id]
    if project_id is not None:
        filters.append(await _env_scope(db, user_id, project_id))
    else:
        filters.append(AutoTestEnvironment.user_id == user_id)
    result = await db.execute(
        select(AutoTestEnvironment).options(selectinload(AutoTestEnvironment.parent)).filter(*filters)
    )
    return result.scalar_one_or_none()


@router.get("")
async def get_all_environments(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_active_project_id),
):
    """获取所有环境（含 parent_id / parent_name，按项目隔离，成员共享）"""
    scope = await _env_scope(db, current_user.id, project_id)
    result = await db.execute(
        select(AutoTestEnvironment)
        .options(selectinload(AutoTestEnvironment.parent))
        .where(scope)
        .order_by(AutoTestEnvironment.created_at)
    )
    envs = result.scalars().all()
    return [_env_to_dict(e) for e in envs]


@router.get("/{env_id}")
async def get_environment(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_active_project_id),
):
    """获取单个环境"""
    env = await _load_env_with_parent(db, env_id, current_user.id, project_id=project_id)
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")
    return _env_to_dict(env)


@router.post("", status_code=201)
async def create_environment(
    env_in: AutoTestEnvironmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_active_project_id_member),
):
    """创建环境（支持 parent_id 设置父环境实现变量继承）"""
    data = env_in.model_dump()
    if "name" in data:
        data["env_name"] = data.pop("name")

    # 校验 parent_id 合法性（不形成循环、不超深度、父环境存在）
    try:
        await validate_parent_id(db, env_id=None, parent_id=data.get("parent_id"), user_id=current_user.id)
    except InheritanceError as exc:
        _raise_inheritance_error(exc)

    scope = await _env_scope(db, current_user.id, project_id)
    if data.get("is_default"):
        await db.execute(update(AutoTestEnvironment).where(scope).values(is_default=False))

    data["user_id"] = current_user.id
    data["project_id"] = int(project_id)
    env = AutoTestEnvironment(**data)
    db.add(env)
    await db.commit()
    # 重新查询以 eager load parent 关系
    env = await _load_env_with_parent(db, env.id, current_user.id, project_id=project_id)
    return _env_to_dict(env)


@router.put("/{env_id}")
async def update_environment(
    env_id: int,
    env_in: AutoTestEnvironmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_active_project_id_member),
):
    """更新环境（支持修改 parent_id，会校验不形成循环继承）"""
    env = await _load_env_with_parent(db, env_id, current_user.id, project_id=project_id)
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    _set_fields = env_in.model_dump(exclude_unset=True)
    _set_fields.pop("project_id", None)

    # 如果显式传入了 parent_id，校验循环继承与深度
    if "parent_id" in _set_fields:
        try:
            await validate_parent_id(db, env_id=env_id, parent_id=_set_fields["parent_id"], user_id=current_user.id)
        except InheritanceError as exc:
            _raise_inheritance_error(exc)

    scope = await _env_scope(db, current_user.id, project_id)
    if _set_fields.get("is_default"):
        await db.execute(
            update(AutoTestEnvironment)
            .where(
                AutoTestEnvironment.id != env_id,
                scope,
            )
            .values(is_default=False)
        )
    if getattr(env, "project_id", None) is None:
        env.project_id = int(project_id)

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
    # 重新查询以 eager load 最新的 parent 关系
    env = await _load_env_with_parent(db, env_id, current_user.id, project_id=project_id)
    return _env_to_dict(env)


@router.delete("/{env_id}")
async def delete_environment(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_active_project_id_member),
):
    """删除环境"""
    env = await _load_env_with_parent(db, env_id, current_user.id, project_id=project_id)
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    await db.delete(env)
    await db.commit()
    return {"success": True, "message": "删除成功"}


@router.get("/{env_id}/effective-variables")
async def get_effective_variables_endpoint(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取环境合并后的有效变量（含来源标注）。

    返回继承链上所有环境变量合并后的结果，子环境覆盖父环境同名变量。
    每个变量附带 source_environment_id / source_environment_name / is_overridden 字段。
    """
    # 校验环境在当前用户可见范围（兼容旧路径：无 project header 时按 user）
    result = await db.execute(
        select(AutoTestEnvironment).filter(
            AutoTestEnvironment.id == env_id, AutoTestEnvironment.user_id == current_user.id
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    try:
        effective_vars = await get_effective_variables(db, env_id, user_id=current_user.id)
    except InheritanceError as exc:
        _raise_inheritance_error(exc)

    return {
        "env_id": env_id,
        "env_name": env.env_name,
        "variables": [
            {**item, "value": "****" if _SENSITIVE_PATTERN.search(item["name"]) else item["value"]}
            for item in effective_vars
        ],
        "count": len(effective_vars),
    }


@router.get("/{env_id}/inheritance-chain")
async def get_inheritance_chain_endpoint(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取环境继承链（从根环境到当前环境）。

    返回列表中每个元素包含 id / env_name / parent_id / depth（0=根环境）。
    用于前端可视化继承关系，或调试变量覆盖来源。
    """
    # 校验环境归属当前用户
    result = await db.execute(
        select(AutoTestEnvironment).filter(
            AutoTestEnvironment.id == env_id, AutoTestEnvironment.user_id == current_user.id
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    try:
        chain = await get_inheritance_chain(db, env_id, user_id=current_user.id)
    except InheritanceError as exc:
        _raise_inheritance_error(exc)

    items = []
    for depth, e in enumerate(chain):
        items.append(
            {
                "id": e.id,
                "env_name": e.env_name,
                "name": e.env_name,
                "parent_id": e.parent_id,
                "depth": depth,
            }
        )

    return {
        "env_id": env_id,
        "env_name": env.env_name,
        "chain": items,
        "depth": len(items),
    }
