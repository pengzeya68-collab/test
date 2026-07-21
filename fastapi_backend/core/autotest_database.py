"""
AutoTest 数据库模块（已合并到主数据库）

所有 AutoTest 模型现在使用主数据库的 Base 和 engine，
此模块保留仅为向后兼容，所有符号都从 core.database 重导出。
"""

import logging

from fastapi_backend.core.database import (
    AsyncSession,
    AsyncSessionLocal,
    async_session,
    engine,
    get_db,
)

_logger = logging.getLogger(__name__)

__all__ = [
    "AsyncSession",
    "AsyncSessionLocal",
    "async_session",
    "engine",
    "get_autotest_db",
    "get_db",
    "init_autotest_db",
]

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
                "api_doc_shares",
            }
            return bool(autotest_tables & set(existing))

        tables_found = await conn.run_sync(_tables_exist)

        if tables_found:
            if settings.ENVIRONMENT == "production":
                # Production schema changes are exclusively owned by Alembic.
                # Running create_all/ALTER TABLE in every API process races in
                # multi-instance PostgreSQL deployments and can leave partial DDL.
                _logger.info("AutoTest 数据库已存在；生产环境跳过所有运行时 DDL。")
                return
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

                # scenario_steps: step_type, step_config, parent_step_id, pre_script, post_script, pre_script_language, post_script_language
                if "scenario_steps" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("scenario_steps")]
                    migrations = [
                        ("step_type", "VARCHAR(20) DEFAULT 'api_request'"),
                        ("step_config", "JSON"),
                        ("parent_step_id", "INTEGER"),
                        ("pre_script", "TEXT"),
                        ("post_script", "TEXT"),
                        ("pre_script_language", "VARCHAR(20) DEFAULT 'javascript'"),
                        ("post_script_language", "VARCHAR(20) DEFAULT 'javascript'"),
                    ]
                    for col_name, col_type in migrations:
                        if col_name not in cols:
                            sync_conn.execute(text(f"ALTER TABLE scenario_steps ADD COLUMN {col_name} {col_type}"))
                            _logger.info(f"已为 scenario_steps 表添加 {col_name} 列")

                # api_cases: pre_script, post_script, response_schema, current_version, pre_script_language, post_script_language
                if "api_cases" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("api_cases")]
                    migrations = [
                        ("pre_script", "TEXT"),
                        ("post_script", "TEXT"),
                        ("response_schema", "JSON"),
                        ("current_version", "VARCHAR(50)"),
                        ("pre_script_language", "VARCHAR(20) DEFAULT 'javascript'"),
                        ("post_script_language", "VARCHAR(20) DEFAULT 'javascript'"),
                        ("request_config", "JSON"),
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
                    # environments: parent_id（环境变量继承机制）
                    if "parent_id" not in cols:
                        sync_conn.execute(text("ALTER TABLE environments ADD COLUMN parent_id INTEGER"))
                        _logger.info("已为 environments 表添加 parent_id 列（环境变量继承）")
                        # 尝试添加外键约束（PostgreSQL/MySQL 支持，SQLite 跳过）
                        # 注意：PG 在事务中执行 ALTER 失败会污染整个事务，必须用 savepoint 隔离
                        if insp.dialect.name != "sqlite":
                            existing_env_fk = sync_conn.execute(
                                text(
                                    "SELECT 1 FROM pg_constraint WHERE conname = 'fk_environments_parent' "
                                    "AND conrelid = 'environments'::regclass"
                                )
                            ).scalar()
                            if not existing_env_fk:
                                try:
                                    sp = sync_conn.begin_nested()
                                    sync_conn.execute(
                                        text(
                                            "ALTER TABLE environments ADD CONSTRAINT "
                                            "fk_environments_parent FOREIGN KEY (parent_id) "
                                            "REFERENCES environments(id) ON DELETE SET NULL"
                                        )
                                    )
                                    sp.commit()
                                except Exception:
                                    sp.rollback()
                                    pass
                        # 添加索引加速继承链查询
                        try:
                            sync_conn.execute(
                                text("CREATE INDEX IF NOT EXISTS idx_environments_parent_id ON environments(parent_id)")
                            )
                        except Exception:
                            pass

                # api_groups: description, sort_order, updated_at（树形分组管理）
                if "api_groups" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("api_groups")]
                    group_migrations = [
                        ("description", "TEXT"),
                        ("sort_order", "INTEGER DEFAULT 0"),
                        ("updated_at", "DATETIME"),
                    ]
                    for col_name, col_type in group_migrations:
                        if col_name not in cols:
                            sync_conn.execute(text(f"ALTER TABLE api_groups ADD COLUMN {col_name} {col_type}"))
                            _logger.info(f"已为 api_groups 表添加 {col_name} 列")
                    # 补齐 sort_order 索引（加速排序查询）
                    try:
                        sync_conn.execute(
                            text("CREATE INDEX IF NOT EXISTS idx_api_groups_sort_order ON api_groups(sort_order)")
                        )
                    except Exception:
                        pass

                # audit_logs: 补齐审计日志新增列（username/resource_type/resource_id/
                # resource_name/user_agent/request_path/request_method/error_message）
                if "audit_logs" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("audit_logs")]
                    audit_migrations = [
                        ("username", "VARCHAR(80)"),
                        ("resource_type", "VARCHAR(50)"),
                        ("resource_id", "INTEGER"),
                        ("resource_name", "VARCHAR(500)"),
                        ("user_agent", "VARCHAR(500)"),
                        ("request_path", "VARCHAR(500)"),
                        ("request_method", "VARCHAR(10)"),
                        ("error_message", "TEXT"),
                    ]
                    for col_name, col_type in audit_migrations:
                        if col_name not in cols:
                            sync_conn.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type}"))
                            _logger.info(f"已为 audit_logs 表添加 {col_name} 列")

                # scenario_steps: parent_step_id FK (only add if table and column exist but no FK)
                if "scenario_steps" in existing_tables:
                    if insp.dialect.name != "sqlite":
                        # PostgreSQL/MySQL 支持 ADD CONSTRAINT；SQLite 跳过
                        # 注意：PG 在事务中执行 ALTER 失败会污染整个事务，必须用 savepoint 隔离
                        if "parent_step_id" in [c["name"] for c in insp.get_columns("scenario_steps")]:
                            existing_fk = sync_conn.execute(
                                text(
                                    "SELECT 1 FROM pg_constraint WHERE conname = 'fk_scenario_steps_parent' "
                                    "AND conrelid = 'scenario_steps'::regclass"
                                )
                            ).scalar()
                            if not existing_fk:
                                try:
                                    sp = sync_conn.begin_nested()
                                    sync_conn.execute(
                                        text(
                                            "ALTER TABLE scenario_steps ADD CONSTRAINT fk_scenario_steps_parent "
                                            "FOREIGN KEY (parent_step_id) REFERENCES scenario_steps(id)"
                                        )
                                    )
                                    sp.commit()
                                except Exception:
                                    sp.rollback()
                                    pass

                # ============ RBAC 列迁移 ============
                # roles: code 列（角色代码，大写唯一）
                if "roles" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("roles")]
                    if "code" not in cols:
                        sync_conn.execute(text("ALTER TABLE roles ADD COLUMN code VARCHAR(50)"))
                        _logger.info("已为 roles 表添加 code 列（角色代码）")

                # permissions: action 列（操作类型）
                if "permissions" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("permissions")]
                    if "action" not in cols:
                        sync_conn.execute(text("ALTER TABLE permissions ADD COLUMN action VARCHAR(50)"))
                        _logger.info("已为 permissions 表添加 action 列（操作类型）")

                # api_doc_shares: password_hash 列（可选密码保护）
                if "api_doc_shares" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("api_doc_shares")]
                    if "password_hash" not in cols:
                        sync_conn.execute(text("ALTER TABLE api_doc_shares ADD COLUMN password_hash TEXT"))
                        _logger.info("已为 api_doc_shares 表添加 password_hash 列（分享密码保护）")

                # Database-backed suite foundation. create_all above creates new tables;
                # existing desktop databases still need these additive suite columns.
                if "test_suites" in existing_tables:
                    cols = [c["name"] for c in insp.get_columns("test_suites")]
                    migrations = [
                        ("kind", "VARCHAR(20) NOT NULL DEFAULT 'scenario'"),
                        ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
                        ("legacy_key", "VARCHAR(100)"),
                    ]
                    for col_name, col_type in migrations:
                        if col_name not in cols:
                            sync_conn.execute(text(f"ALTER TABLE test_suites ADD COLUMN {col_name} {col_type}"))
                    try:
                        sync_conn.execute(
                            text(
                                "CREATE UNIQUE INDEX IF NOT EXISTS ix_test_suites_legacy_key "
                                "ON test_suites (legacy_key)"
                            )
                        )
                    except Exception:
                        _logger.warning("Unable to create legacy suite index", exc_info=True)

            await conn.run_sync(_migrate_columns)
            return

        if settings.ENVIRONMENT == "production":
            _logger.critical("AutoTest 数据库表未初始化。请先运行 Alembic 迁移。")
            raise RuntimeError("AutoTest 数据库未初始化，请运行 Alembic 迁移。")

        _logger.warning("AutoTest 数据库表不存在，使用 create_all() 创建。")
        await conn.run_sync(Base.metadata.create_all)
