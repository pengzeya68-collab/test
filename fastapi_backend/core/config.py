"""
配置文件 - 核心配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    # 项目信息
    PROJECT_NAME: str = "接口自动化测试平台"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "零代码接口自动化测试平台，支持填表单添加接口，运行自动化测试，生成测试报告"

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./instance/testmaster.db"

    # JWT配置
    SECRET_KEY: str = "testmaster-dev-secret-key-2024"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
