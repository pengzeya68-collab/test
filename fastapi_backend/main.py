"""
Unified FastAPI entrypoint for the TestMaster platform.

This app is the single public entry. All Flask and legacy AutoTest routes
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
    """Create tables only when AUTO_CREATE_TABLES_ON_STARTUP is explicitly set to 'true' or '1'.
    This prevents bypassing migration system during normal startup."""
    if not getattr(settings, 'AUTO_CREATE_TABLES_ON_STARTUP', False):
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_remove_foreign_keys(conn)


async def _migrate_remove_foreign_keys(conn) -> None:
    """移除 submissions 和 interview_sessions 表中 question_id 的外键约束
    SQLite 不支持 ALTER TABLE DROP CONSTRAINT，需要重建表
    同时添加 submissions.question_source 列"""
    from sqlalchemy import text as sa_text, inspect as sa_inspect

    try:
        def _do_migrate(sync_conn):
            try:
                insp = sa_inspect(sync_conn)
                sub_cols = [c["name"] for c in insp.get_columns("submissions")]
                if "question_source" not in sub_cols:
                    sync_conn.execute(sa_text(
                        "ALTER TABLE submissions ADD COLUMN question_source VARCHAR(20) DEFAULT 'interview_question'"
                    ))
                    _logger.info("[迁移] 已添加 submissions.question_source 列")
            except Exception as e:
                _logger.debug(f"[迁移] 添加 question_source 列时出错（可忽略）: {e}")

            for table_name, fk_col, fk_ref_table in [
                ("submissions", "question_id", "interview_questions"),
                ("interview_sessions", "question_id", "interview_questions"),
            ]:
                try:
                    insp = sa_inspect(sync_conn)
                    fks = insp.get_foreign_keys(table_name)
                    target_fk = None
                    for fk in fks:
                        if fk.get("constrained_columns") and fk_col in fk["constrained_columns"]:
                            if fk.get("referred_table") == fk_ref_table:
                                target_fk = fk
                                break
                    if not target_fk:
                        continue

                    cols_info = insp.get_columns(table_name)
                    col_defs = []
                    for c in cols_info:
                        cd = f'"{c["name"]}" {c["type"]}'
                        if not c.get("nullable", True):
                            cd += " NOT NULL"
                        if c.get("default") is not None:
                            cd += f' DEFAULT {c["default"]}'
                        col_defs.append(cd)

                    pk_info = insp.get_pk_constraint(table_name)
                    if pk_info and pk_info.get("constrained_columns"):
                        pk_cols = ", ".join(f'"{c}"' for c in pk_info["constrained_columns"])
                        col_defs.append(f"PRIMARY KEY ({pk_cols})")

                    remaining_fks = [fk for fk in fks if fk is not target_fk]
                    for fk in remaining_fks:
                        fk_cols = ", ".join(f'"{c}"' for c in fk["constrained_columns"])
                        ref_cols = ", ".join(f'"{c}"' for c in fk["referred_columns"])
                        col_defs.append(
                            f'FOREIGN KEY({fk_cols}) REFERENCES "{fk["referred_table"]}"({ref_cols})'
                        )

                    col_defs_str = ",\n  ".join(col_defs)
                    tmp_name = f"_tmp_migrate_{table_name}"

                    sync_conn.execute(sa_text(f"ALTER TABLE \"{table_name}\" RENAME TO \"{tmp_name}\""))
                    sync_conn.execute(sa_text(
                        f'CREATE TABLE "{table_name}" (\n  {col_defs_str}\n)'
                    ))
                    orig_cols = [c["name"] for c in cols_info]
                    cols_str = ", ".join(f'"{c}"' for c in orig_cols)
                    sync_conn.execute(sa_text(
                        f'INSERT INTO "{table_name}" ({cols_str}) SELECT {cols_str} FROM "{tmp_name}"'
                    ))
                    sync_conn.execute(sa_text(f'DROP TABLE "{tmp_name}"'))

                    idxs = insp.get_indexes(table_name)
                    for idx in idxs:
                        try:
                            idx_cols = ", ".join(f'"{c}"' for c in idx["column_names"])
                            sync_conn.execute(sa_text(
                                f'CREATE INDEX IF NOT EXISTS "{idx["name"]}" ON "{table_name}"({idx_cols})'
                            ))
                        except Exception:
                            pass

                    _logger.info(f"[迁移] 已移除 {table_name}.{fk_col} 的外键约束")
                except Exception as e:
                    _logger.debug(f"[迁移] 处理 {table_name}.{fk_col} 时出错（可忽略）: {e}")

        await conn.run_sync(_do_migrate)
    except Exception as e:
        _logger.debug(f"[迁移] 外键迁移过程出错（可忽略）: {e}")


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
    if settings.AUTO_CREATE_TABLES_ON_STARTUP:
        await create_tables()
    await init_auto_test_runtime()
    from fastapi_backend.services.autotest_task_store import start_cleanup_task, stop_cleanup_task
    start_cleanup_task()
    try:
        yield
    finally:
        stop_cleanup_task()
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
admin_router_group.include_router(ai_config_router)
admin_router_group.include_router(backup_router)

legacy_test_router = APIRouter()
legacy_test_router.include_router(groups_router)
legacy_test_router.include_router(cases_router)
legacy_test_router.include_router(envs_router)
legacy_test_router.include_router(plans_router)
legacy_test_router.include_router(execution_router)

autotest_router = APIRouter()
autotest_router.include_router(autotest_groups_router)
autotest_router.include_router(autotest_cases_router)
autotest_router.include_router(autotest_envs_router)
autotest_router.include_router(autotest_scenarios_router)
autotest_router.include_router(autotest_execution_router)
autotest_router.include_router(autotest_diagnostic_router)
autotest_router.include_router(autotest_global_vars_router)

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

ai_tools_router = APIRouter()
ai_tools_router.include_router(interview_router)
ai_tools_router.include_router(sandbox_router)
ai_tools_router.include_router(ai_tutor_router)
ai_tools_router.include_router(community_router)

app.include_router(admin_router_group)
app.include_router(legacy_test_router)
app.include_router(autotest_router)
app.include_router(learning_router)
app.include_router(ai_tools_router)

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
