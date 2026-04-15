from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import AuthenticationException, ValidationException
from fastapi_backend.deps.auth import get_auth_service, get_current_active_user, require_admin
from fastapi_backend.models.models import User
from fastapi_backend.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from fastapi_backend.schemas.common import MessageResponse
from fastapi_backend.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    body: dict,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    username = body.get("username", "").strip()
    email = body.get("email", "").strip()
    phone = body.get("phone", "").strip()
    password = body.get("password", "")

    if not username or not email or not password:
        raise ValidationException("用户名、邮箱和密码不能为空")
    if len(username) < 3 or len(username) > 20:
        raise ValidationException("用户名长度在 3 到 20 个字符之间")
    if len(password) < 6:
        raise ValidationException("密码长度不能少于6个字符")

    existing = await db.execute(
        select(User).where(
            or_(User.username == username, User.email == email, (User.phone == phone) if phone else False)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名、邮箱或手机号已存在")

    new_user = User(
        username=username,
        email=email,
        phone=phone or None,
        password_hash=AuthService.hash_password(password),
        is_admin=False,
        is_active=True,
        level=1,
        score=0,
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="用户名、邮箱或手机号已存在")
    await db.refresh(new_user)

    return auth_service.create_token_pair(new_user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise AuthenticationException("用户名/邮箱或密码无效")
    return auth_service.create_token_pair(user)


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return AuthService.to_user_response(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token_payload = auth_service.decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(token_payload["sub"])
    except (AuthError, KeyError, ValueError) as exc:
        raise AuthenticationException(str(exc)) from exc

    user = await auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise AuthenticationException("用户不存在或已被禁用")

    return auth_service.create_token_pair(user)


@router.get("/admin-only", response_model=MessageResponse)
async def admin_only_example(current_user: User = Depends(require_admin)):
    return MessageResponse(message=f"Admin access granted for {current_user.username}.")


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_active_user),
):
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "phone": getattr(current_user, "phone", None),
            "level": current_user.level,
            "score": current_user.score,
            "is_active": current_user.is_active,
            "is_admin": current_user.is_admin,
            "created_at": str(current_user.created_at) if current_user.created_at else None,
        }
    }


@router.post("/change-password")
async def change_password(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    old_password = body.get("old_password", "")
    new_password = body.get("new_password", "")

    if not old_password or not new_password:
        raise ValidationException("旧密码和新密码不能为空")

    if len(new_password) < 6:
        raise ValidationException("新密码长度不能少于6个字符")

    from werkzeug.security import check_password_hash, generate_password_hash

    if not check_password_hash(current_user.password_hash, old_password):
        raise AuthenticationException("旧密码不正确")

    current_user.password_hash = generate_password_hash(new_password)
    await db.commit()

    return {"message": "密码修改成功"}


@router.post("/forgot-password")
async def forgot_password(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    忘记密码 - 通过手机号 + 验证码重置密码
    开发阶段验证码固定为 123456
    """
    phone = body.get("phone", "")
    code = body.get("code", "")
    new_password = body.get("new_password", "")

    if not phone or not code or not new_password:
        raise ValidationException("手机号、验证码和新密码不能为空")

    if len(new_password) < 6:
        raise ValidationException("新密码长度不能少于6个字符")

    if code != "123456":
        raise AuthenticationException("验证码错误或已过期")

    stmt = select(User).where(User.phone == phone)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationException("该手机号未注册")

    from werkzeug.security import generate_password_hash
    user.password_hash = generate_password_hash(new_password)
    await db.commit()

    return {"message": "密码重置成功"}
