"""
Core application settings for fastapi_backend.
"""
import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "TestMaster FastAPI Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Async FastAPI backend for the TestMaster platform."
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite+aiosqlite:///./instance/testmaster.db"

    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    AI_PROVIDER: str = "openai"
    AI_API_KEY: Optional[str] = None
    AI_BASE_URL: Optional[str] = None
    AI_MODEL: str = "gpt-4-turbo-preview"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_TOKENS: int = 2000
    AI_TEMPERATURE: float = 0.7

    SANDBOX_DEFAULT_TIMEOUT_SECONDS: int = 3
    SANDBOX_MAX_TIMEOUT_SECONDS: int = 30
    SANDBOX_MAX_OUTPUT_LENGTH: int = 1024 * 10
    SANDBOX_MAX_MEMORY_MB: int = 256
    SANDBOX_ALLOWED_MODULES: List[str] = [
        "math", "random", "datetime", "json", "collections", "itertools",
        "functools", "typing", "re", "string", "statistics", "decimal"
    ]

    HOST: str = "0.0.0.0"
    PORT: int = 5001
    RELOAD: bool = False

    AUTO_CREATE_TABLES_ON_STARTUP: bool = False

    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 465
    EMAIL_SMTP_USER: Optional[str] = None
    EMAIL_SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM_ADDRESS: Optional[str] = None
    EMAIL_USE_SSL: bool = True
    EMAIL_ENABLED: bool = False

    AUTO_TEST_BASE_URL: str = "http://localhost:5001"

    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

if not settings.SECRET_KEY:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("生产环境必须在 .env 中设置 SECRET_KEY")
    else:
        import secrets
        settings.SECRET_KEY = secrets.token_urlsafe(32)
        _logger.warning("开发环境使用自动生成的 SECRET_KEY，生产环境请务必在 .env 中设置")

if settings.ENVIRONMENT == "production":
    localhost_origins = [o for o in settings.CORS_ORIGINS if "localhost" in o or "127.0.0.1" in o]
    if localhost_origins:
        _logger.warning(
            "生产环境 CORS_ORIGINS 包含 localhost 地址: %s，请在 .env 中设置正确的 CORS_ORIGINS",
            localhost_origins,
        )
