from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, field_validator

import re


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str = Field(...)
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须包含字母和数字")
        return v


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须包含字母和数字")
        return v


class ForgotPasswordRequest(BaseModel):
    phone: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须包含字母和数字")
        return v


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
    is_super_admin: bool = False
    role: str
    avatar: str | None = None
    level: int
    score: int
    study_time: int
    created_at: datetime | None = None


class WechatLoginRequest(BaseModel):
    code: str = Field(..., min_length=1, description="微信登录凭证code")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token remaining lifetime in seconds")
    user: CurrentUserResponse
