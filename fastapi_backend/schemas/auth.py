from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="用户名或邮箱")
    password: str = Field(..., min_length=1, description="登录密码")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="刷新令牌")


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: str | None = None
    is_active: bool
    is_admin: bool
    role: str
    avatar: str | None = None
    level: int
    score: int
    study_time: int
    created_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token remaining lifetime in seconds")
    user: CurrentUserResponse
