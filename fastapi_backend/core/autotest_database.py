"""
AutoTest 独立数据库模块

使用 instance/auto_test.db 保持数据兼容性，
通过 FastAPI 依赖注入提供 session。
"""
import asyncio
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

_logger = logging.getLogger(__name__)

INSTANCE_DIR = Path(__file__).resolve().parent.parent.parent / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{INSTANCE_DIR}/auto_test.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 使用独立的 Base，与主数据库不共享 metadata
AutoTestBase = declarative_base()
_schema_checked = False
_schema_lock = asyncio.Lock()

# 便捷的 async_session 上下文管理器（供服务层使用）
async_session = AsyncSessionLocal


async def _ensure_autotest_schema_ready() -> None:
    global _schema_checked
    if _schema_checked:
        return

    async with _schema_lock:
        if _schema_checked:
            return

        async with engine.begin() as conn:
            await conn.run_sync(AutoTestBase.metadata.create_all)
            await conn.run_sync(_check_and_add_missing_columns)
        _schema_checked = True


def _check_and_add_missing_columns(conn):
    # 检查 api_cases 表
    cursor = conn.execute(text("PRAGMA table_info(api_cases)"))
    columns = [row[1] for row in cursor.fetchall()]

    if "params" not in columns:
        _logger.info("Adding params column to api_cases table...")
        try:
            conn.execute(text("ALTER TABLE api_cases ADD COLUMN params TEXT"))
            _logger.info("[OK] params column added")
        except Exception as e:
            _logger.error(f"[ERROR] adding params column: {e}")

    # 检查 test_scenarios 表
    cursor = conn.execute(text("PRAGMA table_info(test_scenarios)"))
    scenario_columns = [row[1] for row in cursor.fetchall()]

    if "project_id" not in scenario_columns:
        _logger.info("Adding project_id column to test_scenarios table...")
        try:
            conn.execute(text("ALTER TABLE test_scenarios ADD COLUMN project_id INTEGER"))
            _logger.info("[OK] project_id column added")
        except Exception as e:
            _logger.error(f"[ERROR] adding project_id column: {e}")

    cursor = conn.execute(text("PRAGMA table_info(scenario_execution_records)"))
    execution_record_columns = [row[1] for row in cursor.fetchall()]

    if "env_id" not in execution_record_columns:
        _logger.info("Adding env_id column to scenario_execution_records table...")
        try:
            conn.execute(text("ALTER TABLE scenario_execution_records ADD COLUMN env_id INTEGER"))
            _logger.info("[OK] env_id column added")
        except Exception as e:
            _logger.error(f"[ERROR] adding env_id column: {e}")

    _repair_builtin_demo_cases(conn)


def _repair_builtin_demo_cases(conn):
    """修复内置演示用例中的失效外部接口配置，避免默认场景长期报假红。"""
    demo_case_fixes = [
        {
            "name": "根据 ID 修改该用户信息",
            "old_url": "https://jsonplaceholder.typicode.com/users/{{new_user_id}}",
            "new_url": "https://httpbin.org/put",
            "headers": '{"Content-Type": "application/json"}',
            "payload": '{"id": "{{new_user_id}}", "name": "TestMaster 超级牛逼"}',
        },
        {
            "name": "GET bearer",
            "old_url": "https://httpbin.org/bearer",
            "new_url": "https://httpbin.org/bearer",
            "headers": '{"Authorization": "Bearer demo-token"}',
            "payload": '{}',
        },
    ]

    for item in demo_case_fixes:
        try:
            conn.execute(
                text(
                    """
                    UPDATE api_cases
                    SET url = :new_url,
                        headers = :headers,
                        payload = :payload,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = :name AND url = :old_url
                    """
                ),
                item,
            )
        except Exception as e:
            _logger.error(f"[ERROR] repairing builtin demo case {item['name']}: {e}")


async def get_autotest_db() -> AsyncSession:
    """AutoTest 数据库依赖注入"""
    await _ensure_autotest_schema_ready()
    async with AsyncSessionLocal() as session:
        yield session


async def init_autotest_db() -> None:
    """
    初始化 AutoTest 数据库。
    
    优先验证表结构是否已存在（应通过 Alembic 迁移创建）。
    create_all() 仅作为开发环境的兜底，生产环境会跳过并报错。
    """
    import fastapi_backend.models.autotest as _  # noqa: F401

    from fastapi_backend.core.config import settings
    from sqlalchemy import inspect as sa_inspect

    async with engine.begin() as conn:
        def _tables_exist(sync_conn):
            insp = sa_inspect(sync_conn)
            existing = insp.get_table_names()
            return len(existing) > 0

        tables_found = await conn.run_sync(_tables_exist)

        if tables_found:
            if settings.ENVIRONMENT != "production":
                _logger.info("AutoTest 数据库检测到现有表，正在补齐缺失的新表。")
                await conn.run_sync(AutoTestBase.metadata.create_all)
            await conn.run_sync(_check_and_add_missing_columns)
            return

        if settings.ENVIRONMENT == "production":
            _logger.critical(
                "AutoTest 数据库表未初始化。请先运行 Alembic 迁移创建 auto_test.db 表结构。"
            )
            raise RuntimeError("AutoTest 数据库未初始化，请运行 Alembic 迁移。")

        _logger.warning(
            "AutoTest 数据库表不存在，使用 create_all() 创建。"
            "生产环境请通过 Alembic 管理 auto_test.db 表结构。"
        )
        await conn.run_sync(AutoTestBase.metadata.create_all)
        await conn.run_sync(_check_and_add_missing_columns)
