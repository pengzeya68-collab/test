"""
RBAC 权限检查核心模块

提供基于角色-权限的细粒度访问控制：
- ``PermissionChecker``：可调用依赖，校验当前用户是否有所需权限
- ``require_permissions``：便捷构造（AND 逻辑，需满足全部）
- ``require_any_permission``：便捷构造（OR 逻辑，满足任一即可）
- ``get_user_permissions``：聚合用户所有角色的权限代码集合

设计要点：
1. 复用现有 ``get_current_user`` 认证依赖
2. 同时兼容旧 ``User.role_id``（单角色）与新 ``UserRole`` 多对多关联
3. ADMIN 角色（含 ``is_super_admin`` / 旧 ``is_admin`` 无角色者）短路放行
4. 向后兼容：用户未分配任何角色时，默认给予 TESTER 权限，避免锁死
5. 支持 ``*`` 通配权限与 ``module:*`` 模块通配
"""

from __future__ import annotations

import logging
from typing import Iterable

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import AuthorizationException
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import Permission, Role, RolePermissionMapping, User, UserRole

_logger = logging.getLogger(__name__)

# 系统管理员角色代码（命中即放行全部权限）
ADMIN_ROLE_CODES = {"ADMIN", "admin"}
# 默认回退角色代码（用户无角色时使用的权限集）
DEFAULT_ROLE_CODE = "TESTER"


async def _collect_user_role_ids(user: User, db: AsyncSession) -> list[int]:
    """聚合用户的所有角色 ID（兼容旧 role_id 与新 UserRole 多对多）。"""
    role_ids: set[int] = set()
    # 1. 旧的单角色字段
    if user.role_id:
        role_ids.add(user.role_id)
    # 2. 新的多对多关联表
    result = await db.execute(select(UserRole.role_id).where(UserRole.user_id == user.id))
    for row in result.all():
        role_ids.add(row[0])
    return list(role_ids)


async def _get_role_codes(role_ids: list[int], db: AsyncSession) -> set[str]:
    """根据角色 ID 集合获取角色代码集合（code 为空时回退到 name）。"""
    if not role_ids:
        return set()
    result = await db.execute(select(Role.code, Role.name).where(Role.id.in_(role_ids)))
    codes: set[str] = set()
    for code, name in result.all():
        codes.add(code or name or "")
    return codes


async def get_user_permissions(user: User, db: AsyncSession) -> set[str]:
    """聚合用户所有角色的权限代码集合。

    - 管理员短路：``is_super_admin`` 或旧 ``is_admin``（无 role_id）返回 ``{"*"}``
    - 命中 ADMIN 角色代码返回 ``{"*"}``
    - 无任何角色时回退到 TESTER 角色权限（避免锁死）
    - 否则聚合所有角色对应的权限代码
    """
    # 管理员短路放行
    if user.is_super_admin:
        return {"*"}
    if user.is_admin and user.role_id is None and not await _has_user_roles(user, db):
        return {"*"}

    role_ids = await _collect_user_role_ids(user, db)
    role_codes = await _get_role_codes(role_ids, db)

    # ADMIN 角色短路
    if role_codes & ADMIN_ROLE_CODES:
        return {"*"}

    # 无角色 → 回退到默认角色（TESTER）的权限，避免锁死
    if not role_ids:
        default_role_result = await db.execute(
            select(Role.id).where((Role.code == DEFAULT_ROLE_CODE) | (Role.name == "tester"))
        )
        default_role_id = default_role_result.scalar_one_or_none()
        if default_role_id:
            role_ids = [default_role_id]
            role_codes = {DEFAULT_ROLE_CODE}
        else:
            # 预置角色尚未初始化，给予空权限（初始化后即恢复）
            return set()

    if not role_ids:
        return set()

    # 聚合权限代码
    result = await db.execute(
        select(Permission.code)
        .join(RolePermissionMapping, Permission.id == RolePermissionMapping.permission_id)
        .where(RolePermissionMapping.role_id.in_(role_ids))
    )
    return {row[0] for row in result.all()}


async def _has_user_roles(user: User, db: AsyncSession) -> bool:
    """用户是否在 user_roles 表中存在记录。"""
    result = await db.execute(
        select(UserRole.role_id).where(UserRole.user_id == user.id).limit(1)
    )
    return result.first() is not None


def _has_permission(
    required: str,
    user_permissions: Iterable[str],
) -> bool:
    """检查单个权限是否被满足（支持 ``*`` 与 ``module:*`` 通配）。"""
    perm_set = set(user_permissions)
    if "*" in perm_set:
        return True
    if required in perm_set:
        return True
    # 模块通配：case:* 覆盖 case:create 等
    module_wildcard = required.split(":")[0] + ":*"
    return module_wildcard in perm_set


class PermissionChecker:
    """权限检查依赖类。

    用法::

        require_perm = PermissionChecker(["case:create"])

        @router.post("/cases")
        async def create_case(user: User = Depends(require_perm)):
            ...

    :param required_permissions: 所需权限代码列表
    :param mode: 校验模式，``"all"`` 表示需全部满足，``"any"`` 表示满足任一即可
    """

    def __init__(self, required_permissions: list[str], mode: str = "all"):
        if mode not in ("all", "any"):
            raise ValueError("mode 仅支持 'all' 或 'any'")
        self.required_permissions = required_permissions
        self.mode = mode

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        user_permissions = await get_user_permissions(current_user, db)

        # 通配符 * 直接放行
        if "*" in user_permissions:
            return current_user

        if self.mode == "any":
            # 满足任一即可
            if any(_has_permission(p, user_permissions) for p in self.required_permissions):
                return current_user
            missing = self.required_permissions
        else:
            # 需全部满足
            missing = [
                p for p in self.required_permissions
                if not _has_permission(p, user_permissions)
            ]
            if not missing:
                return current_user

        _logger.info(
            "权限拒绝: user=%s 需要 %s (mode=%s) 缺少 %s",
            current_user.username,
            self.required_permissions,
            self.mode,
            missing,
        )
        raise AuthorizationException(
            f"权限不足。所需权限：{', '.join(self.required_permissions)}（缺少：{', '.join(missing)}）"
        )


def require_permissions(*perms: str):
    """构造权限检查依赖（AND 逻辑：必须拥有全部指定权限）。

    等价于 ``PermissionChecker(list(perms), mode="all")``。
    """
    return PermissionChecker(list(perms), mode="all")


def require_any_permission(*perms: str):
    """构造权限检查依赖（OR 逻辑：满足任一指定权限即可）。"""
    return PermissionChecker(list(perms), mode="any")


# 便于路由直接复用的常见权限检查器（避免重复构造）
# 注意：每个调用返回独立实例，FastAPI 依赖注入要求可调用对象。
require_admin_perm = require_permissions("role:read", "user:read")
