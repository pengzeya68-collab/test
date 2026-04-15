"""
Unified FastAPI entrypoint for the TestMaster platform.

This app is the single public entry. All Flask and legacy AutoTest routes
have been natively migrated — no bridge middleware is needed.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi_backend.core.config import settings
from fastapi_backend.core.database import Base, engine
from fastapi_backend.core.exceptions import BusinessException
from fastapi_backend.routers.admin import router as admin_router
from fastapi_backend.routers.admin_manage import router as admin_manage_router
from fastapi_backend.routers.auth import router as auth_router
from fastapi_backend.routers.cases import router as cases_router
from fastapi_backend.routers.community import router as community_router
from fastapi_backend.routers.environments import router as envs_router
from fastapi_backend.routers.exam import router as exam_router
from fastapi_backend.routers.exercises import router as exercises_router
from fastapi_backend.routers.ai_tutor import router as ai_tutor_router
from fastapi_backend.routers.ai_config import router as ai_config_router
from fastapi_backend.routers.backup import router as backup_router
from fastapi_backend.routers.execution import router as execution_router
from fastapi_backend.routers.exercise import router as exercise_router
from fastapi_backend.routers.groups import router as groups_router
from fastapi_backend.routers.interview import router as interview_router
from fastapi_backend.routers.learning_paths import router as learning_paths_router
from fastapi_backend.routers.plans import router as plans_router
from fastapi_backend.routers.sandbox import router as sandbox_router
from fastapi_backend.routers.skills import router as skills_router
from fastapi_backend.routers.assessment import router as assessment_router
from fastapi_backend.routers.achievements import router as achievements_router
from fastapi_backend.routers.checkin import router as checkin_router
from fastapi_backend.routers.leaderboard import router as leaderboard_router
from fastapi_backend.routers.report import router as report_router
from fastapi_backend.routers.notes import router as notes_router
from fastapi_backend.routers.certificates import router as certificates_router

# AutoTest 原生路由（Phase B 迁移）
from fastapi_backend.routers.autotest_groups import router as autotest_groups_router
from fastapi_backend.routers.autotest_cases import router as autotest_cases_router
from fastapi_backend.routers.autotest_environments import router as autotest_envs_router
from fastapi_backend.routers.autotest_scenarios import router as autotest_scenarios_router
from fastapi_backend.routers.autotest_execution import router as autotest_execution_router
from fastapi_backend.routers.autotest_diagnostic import router as autotest_diagnostic_router
from fastapi_backend.routers.autotest_global_variables import router as autotest_global_vars_router

from fastapi_backend.schemas.common import ErrorResponse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"


async def create_tables() -> None:
    """Create tables only when AUTO_CREATE_TABLES_ON_STARTUP is explicitly set to 'true' or '1'.
    This prevents bypassing migration system during normal startup."""
    if not getattr(settings, 'AUTO_CREATE_TABLES_ON_STARTUP', False):
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

    # 启动调度器并从数据库恢复定时任务（Cron / Webhook 等）
    from fastapi_backend.services.autotest_scheduler import start_scheduler
    start_scheduler()
    await restore_scheduler_jobs_from_db()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.AUTO_CREATE_TABLES_ON_STARTUP:
        await create_tables()
    await init_auto_test_runtime()
    try:
        yield
    finally:
        from fastapi_backend.services.autotest_scheduler import stop_scheduler
        stop_scheduler()


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
    import logging
    _logger = logging.getLogger(__name__)
    _logger.exception(f"未处理异常: {type(exc).__name__}")

    detail = "Internal server error"
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
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Trace-ID", "X-Request-ID"],
)

# ========== Legacy routes (Phase A migrated) ==========
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_manage_router)
app.include_router(groups_router)
app.include_router(cases_router)
app.include_router(envs_router)
app.include_router(plans_router)
app.include_router(execution_router)
app.include_router(interview_router)
app.include_router(sandbox_router)
app.include_router(exercise_router)
app.include_router(community_router)
app.include_router(learning_paths_router)
app.include_router(skills_router)
app.include_router(assessment_router)
app.include_router(achievements_router)
app.include_router(checkin_router)
app.include_router(leaderboard_router)
app.include_router(report_router)
app.include_router(notes_router)
app.include_router(certificates_router)
app.include_router(exam_router)
app.include_router(exercises_router)
app.include_router(ai_tutor_router)
app.include_router(ai_config_router)

# ========== AutoTest native routes (Phase B migrated) ==========
app.include_router(autotest_groups_router)
app.include_router(autotest_cases_router)
app.include_router(autotest_envs_router)
app.include_router(autotest_scenarios_router)
app.include_router(autotest_execution_router)
app.include_router(autotest_diagnostic_router)
app.include_router(autotest_global_vars_router)

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
