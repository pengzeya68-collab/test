"""
Core application settings for fastapi_backend.
"""
import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # 基础配置
    PROJECT_NAME: str = "TestMaster FastAPI Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Async FastAPI backend for the TestMaster platform."
    ENVIRONMENT: str = "development"  # development, production, testing

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./instance/testmaster.db"

    # JWT配置 - 生产环境务必通过 .env 文件设置 SECRET_KEY
    SECRET_KEY: str = "testmaster-dev-secret-key-2024"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # AI配置
    AI_PROVIDER: str = "openai"  # openai, anthropic, azure, etc.
    AI_API_KEY: Optional[str] = None
    AI_BASE_URL: Optional[str] = None
    AI_MODEL: str = "gpt-4-turbo-preview"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_TOKENS: int = 2000
    AI_TEMPERATURE: float = 0.7

    # 沙盒配置
    SANDBOX_DEFAULT_TIMEOUT_SECONDS: int = 3
    SANDBOX_MAX_TIMEOUT_SECONDS: int = 30
    SANDBOX_MAX_OUTPUT_LENGTH: int = 1024 * 10  # 10KB 最大输出长度
    SANDBOX_MAX_MEMORY_MB: int = 256
    SANDBOX_ALLOWED_MODULES: List[str] = [
        "math", "random", "datetime", "json", "collections", "itertools",
        "functools", "typing", "re", "string", "statistics", "decimal"
    ]

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 5001
    RELOAD: bool = False

    # 数据库自动建表开关（生产环境应始终为 False）
    AUTO_CREATE_TABLES_ON_STARTUP: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "testmaster-dev-secret-key-2024":
    _logger.critical("⚠️ 生产环境使用了默认 SECRET_KEY！请立即在 .env 中设置自定义 SECRET_KEY")
