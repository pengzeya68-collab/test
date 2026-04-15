from fastapi import Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import AuthenticationException, AuthorizationException
from fastapi_backend.models.models import User
from fastapi_backend.services.auth_service import AuthError, AuthService


def get_auth_service() -> AuthService:
    return AuthService()


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
        payload = auth_service.decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (AuthError, KeyError, ValueError) as exc:
        raise AuthenticationException(str(exc)) from exc

    user = await auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise AuthenticationException("用户不存在或已被禁用")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def _resolve_role(user: User) -> str:
    return user.role


def require_role(*allowed_roles: str):
    normalized_roles = {role.strip().lower() for role in allowed_roles if role and role.strip()}

    async def role_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        user_role = _resolve_role(current_user)
        if user_role not in normalized_roles:
            allowed_display = ", ".join(sorted(normalized_roles))
            raise AuthorizationException(f"权限不足。所需角色：{allowed_display}")
        return current_user

    return role_dependency


async def require_admin(current_user: User = Depends(require_role("admin"))) -> User:
    return current_user


async def require_user_or_admin(current_user: User = Depends(require_role("user", "admin"))) -> User:
    return current_user


async def require_user(current_user: User = Depends(require_role("user"))) -> User:
    """仅允许普通用户访问（管理员不可访问）"""
    return current_user
