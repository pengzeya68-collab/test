"""
SQLite -> PostgreSQL 数据迁移脚本

用法:
    python -m fastapi_backend.scripts.migrate_sqlite_to_postgres [--reset]

功能:
    1. 读取 instance/testmaster.db 和 instance/auto_test.db 中的所有数据
    2. 按外键依赖顺序插入到 PostgreSQL
    3. 自动将 SQLite 中的 datetime 字符串转换为 Python datetime 对象
    4. 自动将 SQLite 中的 JSON 字符串转换为 Python dict/list 对象
    5. 自动处理 SQLite 和 PostgreSQL 之间的列差异（只插入两边都有的列）
    6. 幂等：已存在的数据会跳过
    7. --reset：清空所有目标表后再迁移
"""
import asyncio
import sys
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
_logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INSTANCE_DIR = PROJECT_ROOT / "instance"

MAIN_DB_PATH = INSTANCE_DIR / "testmaster.db"
AUTOTEST_DB_PATH = INSTANCE_DIR / "auto_test.db"

RESET_MODE = "--reset" in sys.argv


def get_sqlite_tables(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'alembic%'"
    )
    return [row[0] for row in cursor.fetchall()]


def get_sqlite_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    try:
        cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
        return [row[1] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def get_table_data(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    try:
        cursor = conn.execute(f"SELECT * FROM [{table_name}]")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


TABLE_ORDER = [
    "roles",
    "permissions",
    "role_permissions",
    "users",
    "learning_paths",
    "exercises",
    "lesson_sections",
    "progress",
    "posts",
    "comments",
    "likes",
    "favorites",
    "notes",
    "interview_questions",
    "interview_test_cases",
    "interview_sessions",
    "submissions",
    "exercise_submissions",
    "exams",
    "exam_questions",
    "exam_attempts",
    "exam_answers",
    "achievements",
    "user_achievements",
    "daily_checkins",
    "ai_configs",
    "token_blacklist",
    "notifications",
    "interface_test_folders",
    "interface_test_environments",
    "interface_test_cases",
    "interface_test_plans",
    "interface_test_reports",
    "interface_test_report_results",
    "auto_test_groups",
    "project_spaces",
    "project_tasks",
    "project_resources",
    "project_submissions",
    "project_evaluations",
    "api_groups",
    "api_cases",
    "global_variables",
    "environments",
    "test_history",
    "test_scenarios",
    "scenario_steps",
    "test_datasets",
    "scenario_execution_records",
    "performance_scenarios",
    "performance_scenario_steps",
    "performance_execution_records",
    "performance_metrics",
    "test_data_templates",
    "test_data_template_fields",
]

DATETIME_PATTERNS = [
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
]


def _parse_datetime_string(val: str) -> datetime | date | str:
    for pattern in DATETIME_PATTERNS:
        try:
            return datetime.strptime(val, pattern)
        except (ValueError, TypeError):
            continue
    return val


async def _get_pg_column_types(engine) -> dict[str, dict[str, str]]:
    from sqlalchemy import text

    type_map: dict[str, dict[str, str]] = {}
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT table_name, column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "ORDER BY table_name, ordinal_position"
        ))
        for row in result.fetchall():
            table_name, col_name, data_type = row
            if table_name not in type_map:
                type_map[table_name] = {}
            type_map[table_name][col_name] = data_type
    return type_map


async def _get_pg_not_null_columns(engine) -> dict[str, set[str]]:
    from sqlalchemy import text

    not_null_map: dict[str, set[str]] = {}
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT table_name, column_name "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' AND is_nullable = 'NO' "
            "AND column_default IS NULL "
            "AND column_name != 'id' "
            "ORDER BY table_name, column_name"
        ))
        for row in result.fetchall():
            table_name, col_name = row
            if table_name not in not_null_map:
                not_null_map[table_name] = set()
            not_null_map[table_name].add(col_name)
    return not_null_map


COLUMN_DEFAULTS: dict[str, Any] = {
    "item_type": "post",
    "is_active": True,
    "is_public": True,
    "is_published": True,
    "is_approved": True,
    "is_essence": False,
    "is_top": False,
    "is_system": False,
    "is_default": False,
    "is_encrypted": False,
    "is_read": False,
    "status": "active",
    "difficulty": "medium",
    "language": "python",
    "body_type": "none",
    "content_type": "application/json",
    "rule_type": "fixed",
    "test_type": "load",
    "question_type": "short_answer",
    "question_source": "interview_question",
    "execution_status": "pending",
    "ai_evaluation_status": "pending",
    "exam_type": "模拟考试",
    "sort_order": 0,
    "step_order": 0,
    "weight": 1,
    "think_time": 0,
    "progress": 1,
    "row_count": 10,
    "score": 0,
    "threshold": 1,
    "exp_reward": 10,
    "estimated_hours": 10,
    "exercise_count": 0,
    "view_count": 0,
    "like_count": 0,
    "comment_count": 0,
    "collect_count": 0,
    "total_score": 100,
    "pass_score": 60,
    "duration": 60,
    "max_tokens": 2000,
    "timeout_seconds": 60,
    "time_estimate": 15,
    "attempts": 0,
    "stage": 1,
}


def _convert_value(col_name: str, value: Any, pg_types: dict[str, str]) -> Any:
    if value is None:
        return None

    pg_type = pg_types.get(col_name, "")
    pg_type_lower = pg_type.lower()

    if "timestamp" in pg_type_lower:
        if isinstance(value, str):
            parsed = _parse_datetime_string(value)
            if isinstance(parsed, (datetime, date)):
                return parsed
            _logger.warning("Cannot parse datetime for %s: %r", col_name, value)
            return None
        if isinstance(value, (datetime, date)):
            return value
        return None

    if pg_type_lower == "date":
        if isinstance(value, str):
            parsed = _parse_datetime_string(value)
            if isinstance(parsed, (datetime, date)):
                return parsed.date() if isinstance(parsed, datetime) else parsed
            _logger.warning("Cannot parse date for %s: %r", col_name, value)
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return None

    if pg_type_lower in ("jsonb", "json"):
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except (json.JSONDecodeError, TypeError):
                _logger.warning("Cannot parse JSON for %s", col_name)
                return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return None

    if pg_type_lower in ("boolean", "bool"):
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes")
        return value

    return value


def _convert_row(row: dict, pg_types: dict[str, str]) -> dict:
    return {
        col: _convert_value(col, val, pg_types)
        for col, val in row.items()
    }


async def _reset_tables(engine, tables_in_pg: set[str]) -> None:
    from sqlalchemy import text

    _logger.info("Reset mode: truncating all tables...")
    async with engine.begin() as conn:
        for table in reversed(TABLE_ORDER):
            if table in tables_in_pg:
                try:
                    await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))
                    _logger.info("  Truncated: %s", table)
                except Exception as e:
                    _logger.warning("  Failed to truncate %s: %s", table, e)
    _logger.info("All tables truncated.")


async def migrate():
    from sqlalchemy import text
    from fastapi_backend.core.database import engine, AsyncSessionLocal

    _logger.info("=" * 60)
    _logger.info("Starting SQLite -> PostgreSQL migration")
    _logger.info("Reset mode: %s", RESET_MODE)
    _logger.info("=" * 60)

    pg_column_types = await _get_pg_column_types(engine)
    pg_not_null = await _get_pg_not_null_columns(engine)
    tables_in_pg = set(pg_column_types.keys())
    _logger.info("PostgreSQL tables found: %d", len(tables_in_pg))

    if RESET_MODE:
        await _reset_tables(engine, tables_in_pg)

    main_conn = sqlite3.connect(str(MAIN_DB_PATH))
    main_conn.row_factory = sqlite3.Row

    autotest_conn = None
    if AUTOTEST_DB_PATH.exists():
        autotest_conn = sqlite3.connect(str(AUTOTEST_DB_PATH))
        autotest_conn.row_factory = sqlite3.Row

    main_tables = set(get_sqlite_tables(main_conn))
    autotest_tables = set(get_sqlite_tables(autotest_conn)) if autotest_conn else set()

    _logger.info("SQLite main DB tables: %d, AutoTest DB tables: %d", len(main_tables), len(autotest_tables))

    inserted_counts = {}
    error_counts = {}

    for table in TABLE_ORDER:
        sqlite_conn = None
        if table in main_tables:
            sqlite_conn = main_conn
        elif table in autotest_tables:
            sqlite_conn = autotest_conn

        if sqlite_conn is None:
            continue

        if table not in tables_in_pg:
            _logger.warning("Table %s exists in SQLite but not in PostgreSQL, skipping.", table)
            continue

        rows = get_table_data(sqlite_conn, table)
        if not rows:
            inserted_counts[table] = 0
            error_counts[table] = 0
            continue

        pg_types = pg_column_types.get(table, {})
        pg_columns = set(pg_types.keys())
        table_not_null = pg_not_null.get(table, set())

        sqlite_columns = set(rows[0].keys())

        common_columns = [c for c in rows[0].keys() if c in pg_columns]
        extra_sqlite_cols = sqlite_columns - pg_columns
        extra_pg_cols = pg_columns - sqlite_columns

        missing_not_null = []
        for col in extra_pg_cols:
            if col in table_not_null and col not in COLUMN_DEFAULTS:
                missing_not_null.append(col)

        if extra_sqlite_cols:
            _logger.info("  %s: SQLite has extra columns (will skip): %s", table, extra_sqlite_cols)
        if extra_pg_cols:
            _logger.debug("  %s: PG has extra columns (will use defaults): %s", table, extra_pg_cols)
        if missing_not_null:
            _logger.warning("  %s: PG has NOT NULL columns without defaults: %s", table, missing_not_null)

        insert_columns = list(common_columns)
        for col in extra_pg_cols:
            if col in table_not_null and col in COLUMN_DEFAULTS:
                insert_columns.append(col)

        if not insert_columns:
            _logger.warning("  %s: No columns to insert, skipping table.", table)
            inserted_counts[table] = 0
            error_counts[table] = 0
            continue

        col_list = ", ".join(f'"{c}"' for c in insert_columns)
        placeholders_list = []
        for c in insert_columns:
            pg_type_lower = pg_types.get(c, "").lower()
            if pg_type_lower in ("jsonb", "json"):
                placeholders_list.append(f"CAST(:{c} AS jsonb)")
            else:
                placeholders_list.append(f":{c}")
        placeholders = ", ".join(placeholders_list)

        insert_sql = text(
            f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
        )

        inserted = 0
        errors = 0
        for row in rows:
            filtered_row = {c: row[c] for c in common_columns}
            for col in extra_pg_cols:
                if col in table_not_null and col in COLUMN_DEFAULTS:
                    filtered_row[col] = COLUMN_DEFAULTS[col]
            converted_row = _convert_row(filtered_row, pg_types)
            try:
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        result = await session.execute(insert_sql, converted_row)
                        inserted += result.rowcount
            except Exception as e:
                errors += 1
                if errors <= 3:
                    _logger.error("Error inserting into %s (id=%s): %s", table, converted_row.get("id", "?"), str(e)[:200])

        inserted_counts[table] = inserted
        error_counts[table] = errors
        total = len(rows)
        skipped = total - inserted - errors
        status = "OK" if errors == 0 else "ERR"
        _logger.info("  [%s] %s: %d inserted, %d skipped, %d errors (total: %d)", status, table, inserted, skipped, errors, total)

    main_conn.close()
    if autotest_conn:
        autotest_conn.close()

    print("\n" + "=" * 70)
    print("Migration Summary:")
    print("=" * 70)
    total_inserted = sum(inserted_counts.values())
    total_errors = sum(error_counts.values())
    total_tables = len(inserted_counts)
    error_tables = sum(1 for v in error_counts.values() if v > 0)
    print(f"Tables processed: {total_tables}")
    print(f"Total inserted:   {total_inserted}")
    print(f"Total errors:     {total_errors}")
    print(f"Tables with errors: {error_tables}")
    if total_errors > 0:
        print("\nTables with errors:")
        for table, count in error_counts.items():
            if count > 0:
                print(f"  - {table}: {count} errors")
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(migrate())
