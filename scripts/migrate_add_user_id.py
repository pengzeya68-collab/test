"""
数据隔离修复迁移脚本

给所有 AutoTest 表添加 user_id 列，
并将现有数据绑定到 test 账号（user_id=6）
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "testmaster.db"
TEST_USER_ID = 6

# 需要加 user_id 的表
TABLES_WITH_USER_ID = [
    "api_groups",
    "api_cases",
    "global_variables",
    "environments",
    "test_history",
    "test_scenarios",
    "performance_scenarios",
    "mock_projects",
    "test_suites",
    "test_data_templates",  # 已有 user_id
]


def migrate():
    print(f"数据库路径: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"错误: 数据库不存在 {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 获取所有表名
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cur.fetchall()}

    added_count = 0
    bound_count = 0

    for table in TABLES_WITH_USER_ID:
        if table not in existing_tables:
            print(f"  跳过: 表 {table} 不存在")
            continue

        # 检查是否已有 user_id 列
        cur.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in cur.fetchall()}

        if "user_id" in columns:
            print(f"  跳过: {table} 已有 user_id 列")
            # 绑定现有 NULL 数据
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL")
            null_count = cur.fetchone()[0]
            if null_count > 0:
                cur.execute(f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL", (TEST_USER_ID,))
                print(f"  绑定: {table} 更新了 {null_count} 条 NULL user_id → {TEST_USER_ID}")
                bound_count += null_count
            continue

        # 添加 user_id 列
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
            print(f"  添加: {table}.user_id 列")
            added_count += 1
        except sqlite3.OperationalError as e:
            print(f"  错误: 添加 {table}.user_id 失败: {e}")
            continue

        # 绑定现有数据到 test 账号
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total = cur.fetchone()[0]
        if total > 0:
            cur.execute(f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL", (TEST_USER_ID,))
            print(f"  绑定: {table} 中 {total} 条记录 → user_id={TEST_USER_ID}")
            bound_count += total

    # 为 user_id 列创建索引（如果不存在）
    for table in TABLES_WITH_USER_ID:
        if table not in existing_tables:
            continue
        index_name = f"idx_{table}_user_id"
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}(user_id)")
            print(f"  索引: {index_name}")
        except sqlite3.OperationalError as e:
            print(f"  索引跳过: {index_name}: {e}")

    conn.commit()
    conn.close()

    print(f"\n迁移完成!")
    print(f"  新增 user_id 列: {added_count} 个表")
    print(f"  绑定数据到 test(user_id={TEST_USER_ID}): {bound_count} 条记录")


if __name__ == "__main__":
    migrate()
