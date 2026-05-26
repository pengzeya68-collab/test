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
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi_backend.core.config import settings

_logger = logging.getLogger(__name__)
from fastapi_backend.core.database import Base, engine
from fastapi_backend.core.exceptions import BusinessException
from fastapi_backend.routers.admin import router as admin_router
from fastapi_backend.routers.admin_users import router as admin_users_router
from fastapi_backend.routers.admin_exercises import router as admin_exercises_router
from fastapi_backend.routers.admin_paths import router as admin_paths_router
from fastapi_backend.routers.admin_exams import router as admin_exams_router
from fastapi_backend.routers.admin_community import router as admin_community_router
from fastapi_backend.routers.admin_system import router as admin_system_router
from fastapi_backend.routers.admin_system_mgmt import router as admin_system_mgmt_router
from fastapi_backend.routers.auth import router as auth_router
from fastapi_backend.routers.community import router as community_router
from fastapi_backend.routers.exam import router as exam_router
from fastapi_backend.routers.exercises import router as exercises_router
from fastapi_backend.routers.ai_tutor import router as ai_tutor_router
from fastapi_backend.routers.ai_config import router as ai_config_router
from fastapi_backend.routers.backup import router as backup_router
from fastapi_backend.routers.exercise import router as exercise_router
from fastapi_backend.routers.interview import router as interview_router
from fastapi_backend.routers.learning_paths import router as learning_paths_router
from fastapi_backend.routers.sandbox import router as sandbox_router
from fastapi_backend.routers.skills import router as skills_router
from fastapi_backend.routers.assessment import router as assessment_router
from fastapi_backend.routers.achievements import router as achievements_router
from fastapi_backend.routers.checkin import router as checkin_router
from fastapi_backend.routers.leaderboard import router as leaderboard_router
from fastapi_backend.routers.report import router as report_router
from fastapi_backend.routers.notes import router as notes_router
from fastapi_backend.routers.certificates import router as certificates_router
from fastapi_backend.routers.rbac import router as rbac_router
from fastapi_backend.routers.projects import router as projects_router

# AutoTest 原生路由（Phase B 迁移）
from fastapi_backend.routers.autotest_groups import router as autotest_groups_router
from fastapi_backend.routers.autotest_cases import router as autotest_cases_router
from fastapi_backend.routers.autotest_environments import router as autotest_envs_router
from fastapi_backend.routers.autotest_scenarios import router as autotest_scenarios_router
from fastapi_backend.routers.autotest_execution import router as autotest_execution_router
from fastapi_backend.routers.autotest_diagnostic import router as autotest_diagnostic_router
from fastapi_backend.routers.autotest_global_variables import router as autotest_global_vars_router
from fastapi_backend.routers.autotest_jmeter import router as autotest_jmeter_router
from fastapi_backend.routers.autotest_data_factory import router as autotest_data_factory_router
from fastapi_backend.routers.notifications import router as notifications_router
from fastapi_backend.routers.favorites import router as favorites_router
from fastapi_backend.routers.search import router as search_router
from fastapi_backend.routers.tools import router as tools_router
from fastapi_backend.routers.reports import router as reports_router
from fastapi_backend.routers.mock_api import router as mock_api_router
from fastapi_backend.routers.assert_templates import router as assert_templates_router
from fastapi_backend.routers.autotest_diff import router as autotest_diff_router
from fastapi_backend.routers.autotest_suites import router as autotest_suites_router
from fastapi_backend.routers.autotest_health import router as autotest_health_router

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
        _logger.info("已清理 %s 中 %d 个过期临时文件（超过 %d 小时）", directory, removed, max_age_hours)


async def create_tables() -> None:
    """创建数据库表 - 仅用于开发/测试环境快速初始化。
    生产环境务必使用 Alembic 迁移管理数据库变更。"""
    if not getattr(settings, 'AUTO_CREATE_TABLES_ON_STARTUP', False):
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
    from pathlib import Path
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if settings.ENVIRONMENT == "testing":
        yield
        return

    if settings.AUTO_CREATE_TABLES_ON_STARTUP:
        await create_tables()
    else:
        await ensure_dev_tables()
    try:
        yield
    finally:
        pass


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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}


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
    import logging
    _logger = logging.getLogger(__name__)
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

# ========== 路由分组注册 ==========
app.include_router(auth_router)

admin_router_group = APIRouter()
admin_router_group.include_router(admin_router)
admin_router_group.include_router(admin_users_router)
admin_router_group.include_router(admin_exercises_router)
admin_router_group.include_router(admin_paths_router)
admin_router_group.include_router(admin_exams_router)
admin_router_group.include_router(admin_community_router)
admin_router_group.include_router(admin_system_router)
admin_router_group.include_router(admin_system_mgmt_router)
admin_router_group.include_router(ai_config_router)
admin_router_group.include_router(backup_router)
admin_router_group.include_router(rbac_router)

autotest_router = APIRouter()
autotest_router.include_router(autotest_groups_router)
autotest_router.include_router(autotest_cases_router)
autotest_router.include_router(autotest_envs_router)
autotest_router.include_router(autotest_scenarios_router)
autotest_router.include_router(autotest_execution_router)
autotest_router.include_router(autotest_diagnostic_router)
autotest_router.include_router(autotest_global_vars_router)
autotest_router.include_router(autotest_jmeter_router)
autotest_router.include_router(autotest_data_factory_router)

learning_router = APIRouter()
learning_router.include_router(learning_paths_router)
learning_router.include_router(skills_router)
learning_router.include_router(assessment_router)
learning_router.include_router(achievements_router)
learning_router.include_router(checkin_router)
learning_router.include_router(leaderboard_router)
learning_router.include_router(report_router)
learning_router.include_router(notes_router)
learning_router.include_router(certificates_router)
learning_router.include_router(exam_router)
learning_router.include_router(exercise_router)
learning_router.include_router(exercises_router)
learning_router.include_router(projects_router)

ai_tools_router = APIRouter()
ai_tools_router.include_router(interview_router)
ai_tools_router.include_router(sandbox_router)
ai_tools_router.include_router(ai_tutor_router)
ai_tools_router.include_router(community_router)

app.include_router(admin_router_group)
app.include_router(autotest_router)
app.include_router(learning_router)
app.include_router(ai_tools_router)
app.include_router(notifications_router)
app.include_router(favorites_router)
app.include_router(search_router)
app.include_router(tools_router)
app.include_router(reports_router)
app.include_router(mock_api_router)
app.include_router(assert_templates_router)
app.include_router(autotest_diff_router)
app.include_router(autotest_suites_router)
app.include_router(autotest_health_router)

# ========== Static files for Allure reports ==========
REPORTS_DIR = AUTOTEST_DATA_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True, parents=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR.resolve()), html=False), name="reports")


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
