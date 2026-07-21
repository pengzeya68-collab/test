"""
Core application settings for fastapi_backend.
"""

import logging
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "TestMaster FastAPI Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Async FastAPI backend for the TestMaster platform."
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://testmaster:@localhost:5432/testmaster"

    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""
    ADMIN_SECRET_KEY: str = ""

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"  # 榛樿浠呭厑璁告湰鍦板墠绔煙鍚?

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS_ORIGINS into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

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
        "math",
        "random",
        "datetime",
        "json",
        "collections",
        "itertools",
        "functools",
        "typing",
        "re",
        "string",
        "statistics",
        "decimal",
    ]

    HOST: str = "0.0.0.0"
    PORT: int = 5001
    RELOAD: bool = False

    AUTO_CREATE_TABLES_ON_STARTUP: bool = False

    # 鍔犲瘑瀵嗛挜锛堢敤浜庡姞瀵嗘暟鎹簱鏁忔劅瀛楁锛?
    TESTMASTER_ENCRYPTION_KEY: str = ""

    REDIS_URL: Optional[str] = None

    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 465
    EMAIL_SMTP_USER: Optional[str] = None
    EMAIL_SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM_ADDRESS: Optional[str] = None
    EMAIL_USE_SSL: bool = True
    EMAIL_ENABLED: bool = False
    EMAIL_ADMIN_TO: Optional[str] = None
    EMAIL_TEST_TO: Optional[str] = None

    AUTO_TEST_BASE_URL: str = "http://localhost:5001"

    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    WECHAT_MINI_APP_ID: str = ""
    WECHAT_MINI_APP_SECRET: str = ""

    AI_RATE_LIMIT_REQUESTS: int = 10  # 姣忕獥鍙ｆ渶澶ц姹傛暟
    AI_RATE_LIMIT_WINDOW_SECONDS: int = 60  # 閫熺巼闄愬埗绐楀彛锛堢锛?

    # 涓存椂寮€鍏筹細鍏抽棴 SSL 楠岃瘉锛堜粎鐢ㄤ簬寮€鍙?娴嬭瘯鐜锛岀敓浜х幆澧冨繀椤诲紑鍚級
    DISABLE_SSL_VERIFY: bool = False
    # 涓存椂寮€鍏筹細鍏抽棴 SSRF 闃叉姢锛堜粎鐢ㄤ簬寮€鍙?娴嬭瘯鐜锛岀敓浜х幆澧冨繀椤诲紑鍚級
    DISABLE_SSRF_GUARD: bool = False
    # 涓存椂寮€鍏筹細鍏抽棴 Nginx 闄愭祦锛堥€氳繃鐜鍙橀噺鎺у埗锛?
    DISABLE_RATE_LIMIT: bool = True

    # JMeter 蹇€熼瑙堟ā寮忎笂闄愶紙淇濇寔鐜扮姸 200/60/10锛屽彲鐢?.env 瑕嗙洊锛?
    JMETER_QUICK_MAX_CONCURRENCY: int = 200
    JMETER_QUICK_MAX_DURATION: int = 60
    JMETER_QUICK_MAX_RAMPUP: int = 10
    # JMeter 寮曟搸 feature flag锛堥粯璁ゅ叧锛岀伆搴﹀垏娴佹椂璁句负 true锛?
    JMETER_ENGINE_ENABLED: bool = False

    # UI 鑷姩鍖?feature flag锛圥hase 0 榛樿寮€鍚紝鍏佽 API 楠ㄦ灦娉ㄥ唽锛?
    UI_AUTOMATION_ENABLED: bool = True
    UI_AUTOMATION_ARTIFACT_MAX_BYTES: int = 10 * 1024 * 1024
    AUTOTEST_QUICK_RUN_TIMEOUT_SECONDS: float = 10.0

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()


def validate_production_database(config: Settings) -> None:
    if config.ENVIRONMENT != "production":
        return
    if not config.DATABASE_URL.lower().startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "Production requires PostgreSQL through a postgresql+asyncpg:// DATABASE_URL; "
            "SQLite is supported only for local development and tests."
        )


validate_production_database(settings)

if settings.ENVIRONMENT == "production":
    unsafe_flags = [
        name
        for name, enabled in (
            ("DISABLE_SSL_VERIFY", settings.DISABLE_SSL_VERIFY),
            ("DISABLE_SSRF_GUARD", settings.DISABLE_SSRF_GUARD),
        )
        if enabled
    ]
    if unsafe_flags:
        raise RuntimeError(f"Production refuses unsafe security flags: {', '.join(unsafe_flags)}")

if not settings.SECRET_KEY:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("鐢熶骇鐜蹇呴』鍦?.env 涓缃?SECRET_KEY")
    else:
        import secrets

        settings.SECRET_KEY = secrets.token_urlsafe(32)
        _logger.warning("开发环境使用随机生成的 SECRET_KEY，生产环境请务必在 .env 中设置固定密钥")

if not settings.ADMIN_PASSWORD:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("鐢熶骇鐜蹇呴』鍦?.env 涓缃?ADMIN_PASSWORD")
    else:
        import secrets

        settings.ADMIN_PASSWORD = secrets.token_urlsafe(16)
        _logger.warning("开发环境使用随机生成的 ADMIN_PASSWORD，生产环境请务必在 .env 中设置固定密码")

# 鑷敤椤圭洰涓嶉檺鍒跺瘑鐮佸己搴︼紝濡傞渶鍔犲己瀹夊叏璇疯嚜琛屼慨鏀?.env 涓殑 ADMIN_PASSWORD

if not settings.ADMIN_SECRET_KEY:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("鐢熶骇鐜蹇呴』鍦?.env 涓缃?ADMIN_SECRET_KEY")
    else:
        import secrets

        settings.ADMIN_SECRET_KEY = secrets.token_urlsafe(32)
        _logger.warning("开发环境使用随机生成的 ADMIN_SECRET_KEY，生产环境请务必在 .env 中设置固定密钥")

if settings.ENVIRONMENT == "production":
    localhost_origins = [o for o in settings.cors_origins_list if "localhost" in o or "127.0.0.1" in o]
    if localhost_origins:
        _logger.warning(
            "鐢熶骇鐜 CORS_ORIGINS 鍖呭惈 localhost 鍦板潃: %s锛岃鍦?.env 涓缃纭殑 CORS_ORIGINS",
            localhost_origins,
        )
