"""
Unified FastAPI entrypoint for the TestMaster platform.

This app is the single public entry. All FastAPI routes
have been natively migrated — no bridge middleware is needed.
"""

from __future__ import annotations

import uuid
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi_backend.core.config import settings

_logger = logging.getLogger(__name__)
from fastapi_backend.core.database import Base, engine
from fastapi_backend.core.exceptions import BusinessException
from sqlalchemy import text

from fastapi_backend.schemas.common import ErrorResponse
from fastapi_backend.middleware.request_stats import request_stats_middleware


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"


def _cleanup_stale_temp_files(directory: Path, max_age_hours: int = 24) -> None:
    import time

    if not directory.exists():
        return
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    for f in directory.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    if removed:
        _logger.info(
            "已清理 %s 中 %d 个过期临时文件（超过 %d 小时）",
            directory,
            removed,
            max_age_hours,
        )


async def create_tables() -> None:
    """创建数据库表 - 仅用于开发/测试环境快速初始化。
    生产环境务必使用 Alembic 迁移管理数据库变更。"""
    if not getattr(settings, "AUTO_CREATE_TABLES_ON_STARTUP", False):
        return
    _logger.warning(
        "⚠️ AUTO_CREATE_TABLES_ON_STARTUP 已启用，正在使用 create_all() 创建表。"
        "生产环境请使用 `alembic upgrade head` 替代此选项。"
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_dev_tables() -> None:
    """在非生产环境补齐主库缺失的新表，不改已有表结构。"""
    if settings.ENVIRONMENT == "production":
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 补齐 audit_logs 表缺失的 detail 列（旧迁移未包含）
        try:
            await conn.execute(text("ALTER TABLE audit_logs ADD COLUMN detail TEXT"))
        except Exception:
            pass  # 列已存在则忽略


async def init_auto_test_runtime() -> None:
    """Initialize AutoTest assets: DB tables, directories, scheduler."""
    from fastapi_backend.core.autotest_database import init_autotest_db
    from fastapi_backend.services.autotest_schedule_persistence import (
        ensure_schedule_columns_on_db,
        restore_scheduler_jobs_from_db,
    )

    # 初始化 AutoTest 独立数据库（受环境变量控制）
    if settings.AUTO_CREATE_TABLES_ON_STARTUP:
        await init_autotest_db()
    await ensure_schedule_columns_on_db()

    # 确保目录存在
    for directory in (
        AUTOTEST_DATA_DIR / "reports",
        AUTOTEST_DATA_DIR / "temp_run_data",
        AUTOTEST_DATA_DIR / "allure-results",
        AUTOTEST_DATA_DIR / "backups",
        AUTOTEST_DATA_DIR / "temp_pytest_tests",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    _cleanup_stale_temp_files(AUTOTEST_DATA_DIR / "temp_pytest_tests", max_age_hours=24)
    _cleanup_stale_temp_files(AUTOTEST_DATA_DIR / "temp_run_data", max_age_hours=24)

    # 启动调度器（SQLAlchemyJobStore 自动持久化 Job，restore 作为安全补充）
    from fastapi_backend.services.autotest_scheduler import start_scheduler

    start_scheduler()
    await restore_scheduler_jobs_from_db()


@asynccontextmanager
async def lifespan(_: FastAPI):
    log_dir = Path(__file__).parent / "autotest_data" / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        log_dir = Path("/tmp/testmaster_logs")
        log_dir.mkdir(parents=True, exist_ok=True)

    if settings.ENVIRONMENT == "testing":
        yield
        return

    if settings.AUTO_CREATE_TABLES_ON_STARTUP:
        await create_tables()
    else:
        await ensure_dev_tables()
    # AutoTest 初始化（失败不阻塞主服务启动）
    try:
        await init_auto_test_runtime()
        from fastapi_backend.services.autotest_task_store import (
            start_cleanup_task,
            stop_cleanup_task,
        )

        start_cleanup_task()
        _cleanup_needed = True
    except Exception as e:
        _logger.warning("AutoTest 初始化失败（不影响主服务）: %s", e)
        _cleanup_needed = False
    try:
        yield
    finally:
        # 关闭 HTTP 客户端连接池
        try:
            from fastapi_backend.services.autotest_request_service import shutdown_http_client
            await shutdown_http_client()
        except Exception as e:
            _logger.warning("HTTP 客户端关闭失败: %s", e)
        if _cleanup_needed:
            try:
                stop_cleanup_task()
                from fastapi_backend.services.autotest_scheduler import stop_scheduler

                stop_scheduler()
            except Exception as e:
                _logger.warning("AutoTest 清理失败: %s", e)


def get_trace_id(request: Request) -> str:
    trace_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID")
    return trace_id or str(uuid.uuid4())


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Unified TestMaster backend — all routes natively served by FastAPI.",
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    payload = ErrorResponse(
        detail=exc.detail,
        code=exc.code,
        trace_id=get_trace_id(request),
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    payload = ErrorResponse(detail=exc.detail, trace_id=get_trace_id(request))
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    if exc.errors():
        first_error = exc.errors()[0]
        field = ".".join(str(loc) for loc in first_error.get("loc", []))
        detail = f"{field}: {first_error.get('msg', 'Validation failed')}"
    else:
        detail = "Validation failed"

    payload = ErrorResponse(
        detail=detail,
        code="VALIDATION_ERROR",
        trace_id=get_trace_id(request),
    )
    return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _logger.exception(f"未处理异常: {type(exc).__name__}: {str(exc)}")

    # 生产环境不返回详细错误信息，防止信息泄露
    from fastapi_backend.core.config import settings

    if settings.ENVIRONMENT == "production":
        detail = "Internal server error"
    else:
        # 开发环境返回详细错误信息便于调试
        detail = f"{type(exc).__name__}: {str(exc)}"

    payload = ErrorResponse(
        detail=detail,
        code="INTERNAL_SERVER_ERROR",
        trace_id=get_trace_id(request),
    )
    return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))


app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Trace-ID", "X-Request-ID"],
)

# 请求统计中间件（必须在 AI 速率限制之前注册）
app.middleware("http")(request_stats_middleware)

from fastapi_backend.middleware.ai_rate_limiter import ai_rate_limit_middleware

# 测试环境跳过 AI 速率限制中间件，避免 429 影响测试
if settings.ENVIRONMENT != "testing":
    app.middleware("http")(ai_rate_limit_middleware)

# ========== 路由自动注册 ==========
from fastapi_backend.core.router_registry import discover_routers

_routers = discover_routers()

for group_name in ("admin", "autotest", "learning", "ai_tools"):
    group_router = _routers.get(group_name)
    if group_router is not None:
        app.include_router(group_router)

for router in _routers.get("standalone", []):
    app.include_router(router)

# ========== Static files for Allure reports ==========
REPORTS_DIR = AUTOTEST_DATA_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True, parents=True)
app.mount(
    "/reports",
    StaticFiles(directory=str(REPORTS_DIR.resolve()), html=True),
    name="reports",
)


@app.get("/api/health")
async def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "message": "Unified FastAPI backend is running",
        "mode": "single-backend",
        "legacy_flask_enabled": False,
        "legacy_autotest_enabled": False,
    }


if __name__ == "__main__":
    uvicorn.run(
        "fastapi_backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        # 排除 autotest_data 目录的热重载，避免临时测试文件引发不必要的重启
        reload_excludes=[
            "**/temp_pytest_tests/**/**",
            "**/autotest_data/allure-results/**/**",
            "**/autotest_data/reports/**/**",
            "**/autotest_data/temp_run_data/**/**",
            "**/autotest_data/backups/**/**",
        ],
    )
