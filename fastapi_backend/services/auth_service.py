import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

import bcrypt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import User
from fastapi_backend.schemas.auth import CurrentUserResponse, TokenResponse


class AuthError(Exception):
    """Raised when token parsing or auth validation fails."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode("utf-8")


class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.access_ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        self.refresh_ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False

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
        stmt = select(User).where(or_(User.username == username, User.email == username))
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

    def decode_token(self, token: str, expected_type: str | None = None) -> dict[str, Any]:
        try:
            header_segment, payload_segment, signature_segment = token.split(".")
        except ValueError as exc:
            raise AuthError("令牌格式无效") from exc

        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected_signature = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()

        try:
            provided_signature = _b64url_decode(signature_segment)
            payload = json.loads(_b64url_decode(payload_segment))
        except Exception as exc:
            raise AuthError("令牌载荷无效") from exc

        if not hmac.compare_digest(provided_signature, expected_signature):
            raise AuthError("令牌签名无效")

        now = int(time.time())
        if int(payload.get("exp", 0)) < now:
            raise AuthError("令牌已过期")

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
        header = {"alg": "HS256", "typ": "JWT"}

        header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        signature_segment = _b64url_encode(
            hmac.new(
                self.secret_key.encode("utf-8"),
                signing_input,
                hashlib.sha256,
            ).digest()
        )
        return f"{header_segment}.{payload_segment}.{signature_segment}"
