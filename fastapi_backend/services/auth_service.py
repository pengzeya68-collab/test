import logging
import secrets
import time
import warnings
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import bcrypt
import hashlib
import jwt
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import User, TokenBlacklist
from fastapi_backend.schemas.auth import CurrentUserResponse, TokenResponse

_logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised when token parsing or auth validation fails."""


_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode("utf-8")


class AuthService:
    _blacklist_max_age_seconds = 86400
    _db_session: Optional[AsyncSession] = None

    def __init__(self, db: Optional[AsyncSession] = None):
        self.secret_key = settings.SECRET_KEY
        self.access_ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        self.refresh_ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        self._db_session = db

    async def add_to_blacklist(self, token: str, token_type: str = "access", user_id: int = None) -> None:
        if not self._db_session:
            _logger.warning("No database session available for token blacklist")
            return

        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            # 从 JWT payload 中提取过期时间，确保黑名单记录与 token 同时过期
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"], options={"verify_exp": False})
                expiry_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            except Exception:
                # 解码失败时回退到固定 24 小时
                expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=self._blacklist_max_age_seconds)

            record = TokenBlacklist(
                token_hash=token_hash,
                token_type=token_type,
                user_id=user_id,
                expires_at=expiry_dt,
            )
            self._db_session.add(record)
            await self._db_session.commit()
        except IntegrityError:
            # 并发竞态：token_hash 唯一约束冲突，说明已存在，忽略即可
            try:
                await self._db_session.rollback()
            except Exception:
                pass
        except Exception as exc:
            _logger.error("token_blacklist DB write failed: %s", exc)
            try:
                await self._db_session.rollback()
            except Exception:
                pass

    async def is_blacklisted(self, token: str) -> bool:
        if not self._db_session:
            return False

        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = await self._db_session.execute(
                select(TokenBlacklist).where(TokenBlacklist.token_hash == token_hash)
            )
            return result.scalar_one_or_none() is not None
        except Exception as exc:
            _logger.error("token_blacklist DB read failed: %s", exc)
            # 数据库异常时保守处理：返回True视为已撤销，阻止请求通过
            # 避免已登出的token在DB故障期间仍可访问系统
            return True

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
                return True
        except Exception:
            pass
        try:
            import werkzeug.security

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r"The '' password method is deprecated.*",
                    category=UserWarning,
                )
                if werkzeug.security.check_password_hash(password_hash, password):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def is_werkzeug_hash(password_hash: str) -> bool:
        return password_hash.startswith(("pbkdf2:", "sha256:"))

    async def migrate_password_if_needed(self, db, user: User, password: str) -> bool:
        if not self.verify_password(password, user.password_hash):
            return False
        if self.is_werkzeug_hash(user.password_hash):
            user.password_hash = self.hash_password(password)
            await db.commit()
            await db.refresh(user)
        return True

    @staticmethod
    def to_user_response(user: User) -> CurrentUserResponse:
        return CurrentUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            is_active=bool(user.is_active),
            is_admin=bool(user.is_admin),
            role="admin" if user.is_admin else "user",
            avatar=user.avatar,
            level=user.level or 0,
            score=user.score or 0,
            study_time=user.study_time or 0,
            created_at=user.created_at,
        )

    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> User | None:
        stmt = (
            select(User)
            .where(or_(User.username == username, User.email == username))
            .options(selectinload(User.role_obj))
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            self.verify_password(password, _DUMMY_HASH)
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def create_token_pair(self, user: User) -> TokenResponse:
        access_token = self._encode_token(user, token_type="access", ttl_seconds=self.access_ttl_seconds)
        refresh_token = self._encode_token(user, token_type="refresh", ttl_seconds=self.refresh_ttl_seconds)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_ttl_seconds,
            user=self.to_user_response(user),
        )

    async def decode_token(self, token: str, expected_type: str | None = None) -> dict[str, Any]:
        if await self.is_blacklisted(token):
            raise AuthError("令牌已被撤销")

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("令牌已过期") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("令牌无效") from exc

        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            raise AuthError(f"令牌类型无效：应为 {expected_type}")

        return payload

    def _encode_token(self, user: User, token_type: str, ttl_seconds: int) -> str:
        now = int(time.time())
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "is_admin": bool(user.is_admin),
            "type": token_type,
            "iat": now,
            "exp": now + ttl_seconds,
            "jti": secrets.token_hex(16),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
