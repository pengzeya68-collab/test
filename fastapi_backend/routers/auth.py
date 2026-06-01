from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import AuthenticationException, ValidationException
from fastapi_backend.deps.auth import (
    get_auth_service,
    get_current_active_user,
    require_admin,
)
from fastapi_backend.models.models import User
from fastapi_backend.schemas.auth import (
    ChangePasswordRequest,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    WechatLoginRequest,
)
from fastapi_backend.schemas.common import MessageResponse
from fastapi_backend.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# 简单的登录速率限制（IP级别）
_login_attempts: dict[str, list[float]] = {}
_LOGIN_RATE_LIMIT = 5  # 最多尝试次数
_LOGIN_RATE_WINDOW = 300  # 时间窗口（秒）


def _check_login_rate_limit(client_ip: str) -> None:
    """检查登录频率限制，超限则抛出异常"""
    import time

    now = time.time()
    attempts = _login_attempts.get(client_ip, [])
    # 清除过期记录
    attempts = [t for t in attempts if now - t < _LOGIN_RATE_WINDOW]
    if len(attempts) >= _LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"登录尝试过于频繁，请 {_LOGIN_RATE_WINDOW // 60} 分钟后再试",
        )
    attempts.append(now)
    _login_attempts[client_ip] = attempts


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
    existing = await db.execute(select(User).where(or_(*conditions)))
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
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(client_ip)

    user = await auth_service.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise AuthenticationException("用户名/邮箱或密码无效")

    await auth_service.migrate_password_if_needed(db, user, payload.password)
    return auth_service.create_token_pair(user)


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return AuthService.to_user_response(current_user)


class LogoutRequest(BaseModel):
    refresh_token: str = ""


@router.post("/logout")
async def logout(
    body: LogoutRequest,
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

    if body.refresh_token:
        try:
            await auth_service.add_to_blacklist(body.refresh_token, token_type="refresh", user_id=current_user.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"吊销 refresh token 失败: {e}", exc_info=True)

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
    import secrets

    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=503, detail="服务暂不可用，请稍后再试")

    # 开发环境使用随机验证码，避免硬编码安全风险
    dev_code = secrets.token_hex(3)  # 6位随机验证码
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


@router.post("/wechat-login", response_model=TokenResponse)
async def wechat_login(
    body: WechatLoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    import httpx
    from fastapi_backend.core.config import settings

    if not settings.WECHAT_MINI_APP_ID or not settings.WECHAT_MINI_APP_SECRET:
        raise HTTPException(status_code=503, detail="微信小程序登录未配置")

    # 使用 POST 请求传递敏感参数，避免 AppSecret 暴露在 URL 中
    url = "https://api.weixin.qq.com/sns/jscode2session"
    post_data = {
        "appid": settings.WECHAT_MINI_APP_ID,
        "secret": settings.WECHAT_MINI_APP_SECRET,
        "js_code": body.code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, data=post_data)
        data = resp.json()

    openid = data.get("openid")
    if not openid:
        raise AuthenticationException("微信登录失败，请稍后重试")

    stmt = select(User).where(User.phone == f"wx_{openid}")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        import secrets

        username = f"wx_{openid[:8]}"
        email = f"{openid[:12]}@wechat.mini"

        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            username = f"wx_{secrets.token_hex(4)}"

        existing_email = await db.execute(select(User).where(User.email == email))
        if existing_email.scalar_one_or_none():
            email = f"{secrets.token_hex(6)}@wechat.mini"

        user = User(
            username=username,
            email=email,
            phone=f"wx_{openid}",
            password_hash=AuthService.hash_password(secrets.token_urlsafe(32)),
            is_admin=False,
            is_active=True,
            level=1,
            score=0,
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="微信用户创建失败")
        await db.refresh(user)

    return auth_service.create_token_pair(user)
