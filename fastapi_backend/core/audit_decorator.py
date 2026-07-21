"""
审计日志装饰器

提供两种使用方式：
1. 装饰器：自动记录路由调用的审计日志（IP/User-Agent/路径/方法、success/failed）。
2. 手动调用：AuditService.log(...)，用于精细控制（如更新操作的 before/after）。

装饰器自动：
- 从 request 中提取 IP、User-Agent、路径、方法
- 从依赖中获取 user_id / username
- 根据函数是否抛异常判断 success/failed，并记录 error_message
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import Any, Callable, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.services.audit_service import AuditService

_logger = logging.getLogger(__name__)

# 常见的“当前用户”参数名
_USER_PARAM_NAMES = ("current_user", "user")
# 常见的 db 参数名
_DB_PARAM_NAMES = ("db", "session")
# 常见的 request 参数名
_REQUEST_PARAM_NAMES = ("request", "req")


def _bind_arguments(func: Callable, args: tuple, kwargs: dict) -> dict:
    """将位置参数和关键字参数绑定到函数签名的参数名。"""
    try:
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)
    except (TypeError, ValueError):
        # 绑定失败时退化为仅使用 kwargs
        return dict(kwargs)


def _find_by_name(arguments: dict, names: tuple) -> Any:
    """按候选名称从参数字典中查找值。"""
    for name in names:
        if name in arguments:
            return arguments[name]
    return None


def _find_current_user(arguments: dict) -> Any:
    """查找当前用户对象（按参数名或属性特征）。"""
    user = _find_by_name(arguments, _USER_PARAM_NAMES)
    if user is not None:
        return user
    # 兜底：按属性特征查找（具有 id 和 username 的对象）
    for value in arguments.values():
        if value is None or isinstance(value, (str, int, float, bool, list, dict)):
            continue
        if hasattr(value, "username") and hasattr(value, "id"):
            return value
    return None


def _resolve_request(arguments: dict) -> Optional[Request]:
    """查找 Request 对象。"""
    req = _find_by_name(arguments, _REQUEST_PARAM_NAMES)
    if isinstance(req, Request):
        return req
    # 兜底：按类型查找
    for value in arguments.values():
        if isinstance(value, Request):
            return value
    return None


def _resolve_db(arguments: dict) -> Optional[AsyncSession]:
    """查找数据库 session 对象。"""
    db = _find_by_name(arguments, _DB_PARAM_NAMES)
    if isinstance(db, AsyncSession):
        return db
    for value in arguments.values():
        if isinstance(value, AsyncSession):
            return value
    return None


def _resolve_resource_id(arguments: dict, resource_type: str, resource_id_param: Optional[str]) -> Optional[int]:
    """从路径参数中解析资源 ID。"""
    # 显式指定的参数名优先
    if resource_id_param and resource_id_param in arguments:
        return _safe_int(arguments[resource_id_param])
    # 尝试常见候选：{resource_type}_id、id、{resource_type}_id 复数等
    candidates = [
        f"{resource_type}_id",
        "id",
        "scenario_id",
        "suite_id",
        "case_id",
        "variable_id",
        "environment_id",
    ]
    seen = set()
    for name in candidates:
        if name in seen:
            continue
        seen.add(name)
        if name in arguments:
            value = _safe_int(arguments[name])
            if value is not None:
                return value
    return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_resource_name(result: Any) -> Optional[str]:
    """从函数返回值中提取资源名称（用于 create/update）。"""
    if result is None:
        return None
    # 字典结果
    if isinstance(result, dict):
        for key in ("name", "resource_name", "scenario_name", "suite_name"):
            if key in result:
                return str(result[key])
        return None
    # 对象结果（SQLAlchemy 模型等）
    name = getattr(result, "name", None)
    if isinstance(name, str):
        return name
    return None


def _extract_resource_id_from_result(result: Any) -> Optional[int]:
    """从函数返回值中提取资源 ID（用于 create 场景，路径参数中没有 id）。"""
    if result is None:
        return None
    if isinstance(result, dict):
        for key in ("id", "resource_id"):
            if key in result:
                return _safe_int(result[key])
        return None
    rid = getattr(result, "id", None)
    return _safe_int(rid)


def audit_log(
    action: str,
    resource_type: str,
    resource_id_param: Optional[str] = None,
) -> Callable:
    """审计日志装饰器。

    参数:
        action: 操作类型（create/update/delete/execute/import/export）
        resource_type: 资源类型（case/scenario/suite/environment/variable/...）
        resource_id_param: 显式指定路径参数名用于解析 resource_id；
            为 None 时自动从常见候选中推断。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            arguments = _bind_arguments(func, args, kwargs)
            request = _resolve_request(arguments)
            db = _resolve_db(arguments)
            current_user = _find_current_user(arguments)

            user_id = getattr(current_user, "id", None) if current_user else None
            username = getattr(current_user, "username", None) if current_user else None

            # 资源 ID 优先从路径参数解析（delete/execute/update 场景）
            resource_id = _resolve_resource_id(arguments, resource_type, resource_id_param)

            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                # 记录失败审计日志后重新抛出，不影响原有异常处理
                await AuditService.log(
                    db=db,
                    user_id=user_id,
                    username=username,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_name=None,
                    request=request,
                    status="failed",
                    error_message=str(exc),
                )
                raise

            # 成功：尝试从返回值补全 resource_id / resource_name（create 场景）
            if resource_id is None:
                resource_id = _extract_resource_id_from_result(result)
            resource_name = _extract_resource_name(result)

            await AuditService.log(
                db=db,
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                request=request,
                status="success",
            )
            return result

        return wrapper

    return decorator
