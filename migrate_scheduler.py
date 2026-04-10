#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化数据库迁移脚本 - 添加定时调度和 Webhook 告警所需的表和字段
执行：python migrate_scheduler.py
"""

import sqlite3
import os

# 实际使用的数据库
project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'auto_test_platform', 'auto_test.db')

print("[INFO] Using database: %s" % db_path)

if not os.path.exists(db_path):
    print("[ERROR] Database file not found: %s" % db_path)
    exit(1)

# 先列出所有表确认
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("\n[INFO] Existing tables (%d):" % len(tables))
for t in sorted(tables):
    print("  - %s" % t)
conn.close()

# SQL 迁移语句 - 根据实际表名调整
# 自动化场景表实际是 test_scenarios，不是 auto_test_plans
# 但是新增的 scheduled_tasks 表按新命名创建
migrations = [
    # 给 test_scenarios (AutoTestPlan) 添加新字段
    "ALTER TABLE test_scenarios ADD COLUMN cron_expression VARCHAR(50);",
    "ALTER TABLE test_scenarios ADD COLUMN webhook_url VARCHAR(500);",
    # 创建定时任务表
    """
    CREATE TABLE IF NOT EXISTS scheduled_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        scenario_id INTEGER NOT NULL REFERENCES test_scenarios(id),
        name VARCHAR(200),
        cron_expression VARCHAR(50) NOT NULL,
        env_id INTEGER REFERENCES environments(id),
        webhook_url VARCHAR(500),
        is_active BOOLEAN DEFAULT 1,
        last_run_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
]

def main():
    print("\n[INFO] Starting database migration...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    success_count = 0
    skip_count = 0

    for i, sql in enumerate(migrations, 1):
        sql = sql.strip()
        if not sql:
            continue
        try:
            print("\n[INFO] Executing SQL %d/%d:" % (i, len(migrations)))
            if len(sql) > 80:
                print("     %s..." % sql[:80])
            else:
                print("     %s" % sql)
            cursor.execute(sql)
            conn.commit()
            print("[OK] Execution successful")
            success_count += 1
        except sqlite3.OperationalError as e:
            error_msg = str(e)
            if "duplicate column name" in error_msg or "already exists" in error_msg:
                print("[WARN] Skipping: %s" % error_msg)
                skip_count += 1
            else:
                print("[ERROR] Execution failed: %s" % error_msg)
                conn.close()
                exit(1)
        except Exception as e:
            print("[ERROR] Execution failed: %s" % str(e))
            conn.close()
            exit(1)

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("[DONE] Database migration completed!")
    print("       Successful: %d" % success_count)
    print("       Skipped: %d (already exists)" % skip_count)
    print("=" * 60)

    # 验证结果
    print("\n[INFO] Verifying results:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查 test_scenarios 表结构
    if 'test_scenarios' in tables:
        cursor.execute("PRAGMA table_info(test_scenarios);")
        columns = cursor.fetchall()
        print("\ntest_scenarios columns:")
        found_cron = False
        found_webhook = False
        for col in columns:
            name = col[1]
            if name == 'cron_expression':
                found_cron = True
                print("  [OK] cron_expression - exists")
            elif name == 'webhook_url':
                found_webhook = True
                print("  [OK] webhook_url - exists")
            else:
                print("  - %s" % name)
    else:
        print("\n[WARN] test_scenarios table not found in database")

    # 检查 scheduled_tasks 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_tasks';")
    result = cursor.fetchone()
    if result:
        print("\n[OK] scheduled_tasks - table created")
    else:
        print("\n[FAIL] scheduled_tasks - table not created")

    conn.close()

if __name__ == '__main__':
    main()
