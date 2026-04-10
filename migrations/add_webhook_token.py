#!/usr/bin/env python3
"""
手动执行数据库迁移：为 test_scenarios 表添加 webhook_token 字段
用于 CI/CD Webhook 外部触发自动化测试
"""

import sqlite3
import os
import sys

# 获取数据库路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 实际数据库在项目根目录的 instance 文件夹
db_path = os.path.join(project_root, 'instance', 'testmaster.db')

print("[Migration] Database path: %s" % db_path)

if not os.path.exists(db_path):
    print("[Error] Database not found: %s" % db_path)
    sys.exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(test_scenarios)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'webhook_token' in column_names:
        print("[OK] webhook_token column already exists, skipping")
    else:
        # 添加字段
        print("[Migration] Adding webhook_token column...")
        cursor.execute("ALTER TABLE test_scenarios ADD COLUMN webhook_token VARCHAR(64)")
        print("[Migration] Creating unique index...")
        cursor.execute("CREATE UNIQUE INDEX ix_test_scenarios_webhook_token ON test_scenarios(webhook_token)")
        conn.commit()
        print("[OK] Column added successfully")

    # 验证结果
    cursor.execute("PRAGMA table_info(test_scenarios)")
    columns = cursor.fetchall()
    print("\n[Result] test_scenarios table columns:")
    for col in columns:
        print("  - %s: %s" % (col[1], col[2]))

    print("\n[Done] Migration completed successfully!")

except Exception as e:
    print("\n[Error] Migration failed: %s" % e)
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()
