"""
AutoTest 数据库模块（已合并到主数据库）

所有 AutoTest 模型现在使用主数据库的 Base 和 engine，
此模块保留仅为向后兼容，所有符号都从 core.database 重导出。
"""
import logging

from fastapi_backend.core.database import (
    Base as AutoTestBase,
    engine,
    AsyncSessionLocal,
    async_session,
    get_db as get_autotest_db,
)

_logger = logging.getLogger(__name__)


async def init_autotest_db() -> None:
    """Initialize AutoTest tables (now part of main database)."""
    import fastapi_backend.models.autotest as _  # noqa: F401
    from fastapi_backend.core.database import Base, engine
    from fastapi_backend.core.config import settings
    from sqlalchemy import inspect as sa_inspect

    async with engine.begin() as conn:
        def _tables_exist(sync_conn):
            insp = sa_inspect(sync_conn)
            existing = insp.get_table_names()
            autotest_tables = {"api_groups", "api_cases", "global_variables", "environments", "test_history", "test_scenarios"}
            return bool(autotest_tables & set(existing))

        tables_found = await conn.run_sync(_tables_exist)

        if tables_found:
            _logger.info("AutoTest 数据库检测到现有表，正在补齐缺失的新表。")
            await conn.run_sync(Base.metadata.create_all)
            # 运行时迁移：为 scenario_execution_records 补齐 user_id 列
            def _migrate_columns(sync_conn):
                insp = sa_inspect(sync_conn)
                if "scenario_execution_records" in insp.get_table_names():
                    cols = [c["name"] for c in insp.get_columns("scenario_execution_records")]
                    if "user_id" not in cols:
                        from sqlalchemy import text
                        sync_conn.execute(text("ALTER TABLE scenario_execution_records ADD COLUMN user_id INTEGER"))
                        _logger.info("已为 scenario_execution_records 表添加 user_id 列")
            await conn.run_sync(_migrate_columns)
            return

        if settings.ENVIRONMENT == "production":
            _logger.critical("AutoTest 数据库表未初始化。请先运行 Alembic 迁移。")
            raise RuntimeError("AutoTest 数据库未初始化，请运行 Alembic 迁移。")

        _logger.warning("AutoTest 数据库表不存在，使用 create_all() 创建。")
        await conn.run_sync(Base.metadata.create_all)
