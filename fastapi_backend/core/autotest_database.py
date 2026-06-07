"""
AutoTest 数据库模块（已合并到主数据库）

所有 AutoTest 模型现在使用主数据库的 Base 和 engine，
此模块保留仅为向后兼容，所有符号都从 core.database 重导出。
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import (
    engine,
    AsyncSessionLocal,
    get_db,
    async_session,
)

_logger = logging.getLogger(__name__)

# 向后兼容别名，供所有 autotest 路由使用
get_autotest_db = get_db


async def init_autotest_db() -> None:
    """Initialize AutoTest tables (now part of main database)."""
    import fastapi_backend.models.autotest as _  # noqa: F401
    from fastapi_backend.core.database import Base
    from fastapi_backend.core.config import settings
    from sqlalchemy import inspect as sa_inspect

    async with engine.begin() as conn:

        def _tables_exist(sync_conn):
            insp = sa_inspect(sync_conn)
            existing = insp.get_table_names()
            autotest_tables = {
                "api_groups",
                "api_cases",
                "global_variables",
                "environments",
                "test_history",
                "test_scenarios",
            }
            return bool(autotest_tables & set(existing))

        tables_found = await conn.run_sync(_tables_exist)

        if tables_found:
            _logger.info("AutoTest 数据库检测到现有表，正在补齐缺失的新表。")
            await conn.run_sync(Base.metadata.create_all)

            # 运行时迁移：为 scenario_execution_records 补齐 user_id 列
            def _migrate_columns(sync_conn):
                from sqlalchemy import text

                insp = sa_inspect(sync_conn)
                existing_tables = set(insp.get_table_names())

                # scenario_execution_records: user_id
                if "scenario_execution_records" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("scenario_execution_records")]
                    if "user_id" not in cols:
                        sync_conn.execute(text("ALTER TABLE scenario_execution_records ADD COLUMN user_id INTEGER"))
                        _logger.info("已为 scenario_execution_records 表添加 user_id 列")

                # scenario_steps: step_type, step_config, parent_step_id, pre_script, post_script
                if "scenario_steps" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("scenario_steps")]
                    migrations = [
                        ("step_type", "VARCHAR(20) DEFAULT 'api_request'"),
                        ("step_config", "JSON"),
                        ("parent_step_id", "INTEGER"),
                        ("pre_script", "TEXT"),
                        ("post_script", "TEXT"),
                    ]
                    for col_name, col_type in migrations:
                        if col_name not in cols:
                            sync_conn.execute(text(f"ALTER TABLE scenario_steps ADD COLUMN {col_name} {col_type}"))
                            _logger.info(f"已为 scenario_steps 表添加 {col_name} 列")

                # api_cases: pre_script, post_script, response_schema
                if "api_cases" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("api_cases")]
                    migrations = [
                        ("pre_script", "TEXT"),
                        ("post_script", "TEXT"),
                        ("response_schema", "JSON"),
                    ]
                    for col_name, col_type in migrations:
                        if col_name not in cols:
                            sync_conn.execute(text(f"ALTER TABLE api_cases ADD COLUMN {col_name} {col_type}"))
                            _logger.info(f"已为 api_cases 表添加 {col_name} 列")

                # environments: services
                if "environments" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("environments")]
                    if "services" not in cols:
                        sync_conn.execute(text("ALTER TABLE environments ADD COLUMN services JSON"))
                        _logger.info("已为 environments 表添加 services 列")

                # scenario_steps: parent_step_id FK (only add if table and column exist but no FK)
                if "scenario_steps" in existing_tables:
                    try:
                        sync_conn.execute(
                            text(
                                "ALTER TABLE scenario_steps ADD CONSTRAINT fk_scenario_steps_parent "
                                "FOREIGN KEY (parent_step_id) REFERENCES scenario_steps(id)"
                            )
                        )
                    except Exception:
                        # FK already exists or not supported, ignore
                        pass

            await conn.run_sync(_migrate_columns)
            return

        if settings.ENVIRONMENT == "production":
            _logger.critical("AutoTest 数据库表未初始化。请先运行 Alembic 迁移。")
            raise RuntimeError("AutoTest 数据库未初始化，请运行 Alembic 迁移。")

        _logger.warning("AutoTest 数据库表不存在，使用 create_all() 创建。")
        await conn.run_sync(Base.metadata.create_all)
