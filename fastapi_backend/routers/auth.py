from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import AuthenticationException, ValidationException
from fastapi_backend.deps.auth import get_auth_service, get_current_active_user, require_admin
from fastapi_backend.models.models import User
from fastapi_backend.schemas.auth import (
    ChangePasswordRequest,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from fastapi_backend.schemas.common import MessageResponse
from fastapi_backend.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    username = body.username.strip()
    email = body.email.strip()
    phone = body.phone.strip()

    if not username or not email or not body.password:
        raise ValidationException("用户名、邮箱和密码不能为空")

    conditions = [User.username == username, User.email == email]
    if phone:
        conditions.append(User.phone == phone)
    existing = await db.execute(
        select(User).where(or_(*conditions))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名、邮箱或手机号已存在")

    new_user = User(
        username=username,
        email=email,
        phone=phone or None,
        password_hash=AuthService.hash_password(body.password),
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
    
    await auth_service.migrate_password_if_needed(db, user, payload.password)
    return auth_service.create_token_pair(user)


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return AuthService.to_user_response(current_user)


@router.post("/logout")
async def logout(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """用户登出，自动吊销当前 access token 及请求体中提供的 refresh token"""
    if authorization:
        scheme, _, access_token = authorization.partition(" ")
        if scheme.lower() == "bearer" and access_token:
            await auth_service.add_to_blacklist(access_token, token_type="access", user_id=current_user.id)

    refresh_token = body.get("refresh_token", "")
    if refresh_token:
        try:
            await auth_service.add_to_blacklist(refresh_token, token_type="refresh", user_id=current_user.id)
        except Exception:
            pass

    return {"message": "登出成功"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token_payload = await auth_service.decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(token_payload["sub"])
    except (AuthError, KeyError, ValueError) as exc:
        raise AuthenticationException(str(exc)) from exc

    await auth_service.add_to_blacklist(payload.refresh_token)

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
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    if not auth_service.verify_password(body.old_password, current_user.password_hash):
        raise AuthenticationException("旧密码不正确")

    current_user.password_hash = auth_service.hash_password(body.new_password)
    await db.commit()

    return {"message": "密码修改成功"}


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    from fastapi_backend.core.config import settings
    
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=503, detail="服务暂不可用，请稍后再试")
    
    dev_code = "123456"
    print(f"[DEV] 开发环境重置密码验证码: {dev_code} (phone={body.phone})")
    
    if body.code.upper() != dev_code:
        raise AuthenticationException("验证码错误或已过期")

    stmt = select(User).where(User.phone == body.phone)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return {"message": "如果该手机号已注册，密码已重置"}

    user.password_hash = AuthService.hash_password(body.new_password)
    await db.commit()

    return {"message": "如果该手机号已注册，密码已重置"}
