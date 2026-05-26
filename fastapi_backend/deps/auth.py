from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import AuthenticationException, AuthorizationException
from fastapi_backend.models.models import Role, User
from fastapi_backend.services.auth_service import AuthError, AuthService


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if not authorization:
        raise AuthenticationException("缺少Authorization请求头")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationException("Authorization请求头格式无效，应为Bearer token")

    try:
        payload = await auth_service.decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (AuthError, KeyError, ValueError) as exc:
        raise AuthenticationException(str(exc)) from exc

    user = await auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise AuthenticationException("用户不存在或已被禁用")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


async def _resolve_role(user: User, db: AsyncSession) -> str:
    if user.is_super_admin:
        return "super_admin"
    if user.is_admin and user.role_id is None:
        return "admin"
    if user.role_id:
        result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = result.scalar_one_or_none()
        if role:
            return role.name
    return "admin" if user.is_admin else "user"


def require_role(*allowed_roles: str):
    normalized_roles = {role.strip().lower() for role in allowed_roles if role and role.strip()}

    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        user_role = await _resolve_role(current_user, db)
        if user_role not in normalized_roles:
            allowed_display = ", ".join(sorted(normalized_roles))
            raise AuthorizationException(f"权限不足。所需角色：{allowed_display}")
        return current_user

    return role_dependency


async def require_admin(current_user: User = Depends(require_role("admin", "super_admin"))) -> User:
    return current_user


async def require_user_or_admin(current_user: User = Depends(require_role("user", "admin", "super_admin"))) -> User:
    return current_user


async def require_user(current_user: User = Depends(require_role("user"))) -> User:
    """仅允许普通用户访问（管理员不可访问）"""
    return current_user


# ============ RBAC 权限检查（新增）============

def require_permission(*required_permissions: str):
    """检查当前用户是否拥有指定权限之一（RBAC 细粒度权限）"""
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # 超级管理员或旧 admin 用户 → 拥有所有权限
        if current_user.is_super_admin:
            return current_user
        if current_user.is_admin and current_user.role_id is None:
            return current_user

        # 查询用户权限（通过角色关联表）
        from sqlalchemy import select
        from fastapi_backend.models.models import Permission, RolePermissionMapping

        if not current_user.role_id:
            raise AuthorizationException("用户未分配角色，请联系管理员")

        result = await db.execute(
            select(Permission.code).join(
                RolePermissionMapping,
                Permission.id == RolePermissionMapping.permission_id,
            ).where(RolePermissionMapping.role_id == current_user.role_id)
        )
        user_permissions = {row[0] for row in result.all()}

        # 通配符 * 表示所有权限
        if "*" in user_permissions:
            return current_user

        # 逐个检查所需权限
        for req_perm in required_permissions:
            if req_perm in user_permissions:
                return current_user
            # 模块级通配符（如 exercise:*）
            module_wildcard = req_perm.split(":")[0] + ":*"
            if module_wildcard in user_permissions:
                return current_user

        raise AuthorizationException(
            f"权限不足。所需权限：{', '.join(required_permissions)}"
        )

    return permission_dependency
