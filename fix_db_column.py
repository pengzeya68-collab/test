#!/usr/bin/env python3
"""
无损修复脚本：添加缺失的 auto_test_steps.extractors 字段
"""

import sqlite3
import os

# 数据库路径 - 根据项目配置，真实路径是 instance/testmaster.db
DB_PATH = r"C:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db"

# 确保使用正确的路径格式
DB_PATH = os.path.abspath(DB_PATH)

print("Checking database file: %s" % DB_PATH)
print("File exists: %s" % os.path.exists(DB_PATH))

if not os.path.exists(DB_PATH):
    print("ERROR: Database file does not exist: %s" % DB_PATH)
    exit(1)

print("Connecting to database...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # 先检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auto_test_steps';")
    table_exists = cursor.fetchone()
    if not table_exists:
        print("ERROR: Table auto_test_steps does not exist!")
        exit(1)

    print("OK: Table auto_test_steps exists, adding extractors column...")

    # 尝试添加缺失的列，类型 TEXT
    cursor.execute("ALTER TABLE auto_test_steps ADD COLUMN extractors TEXT;")
    conn.commit()
    print("SUCCESS: extractors column added to auto_test_steps table.")
    print("Existing data has NULL for this column, no data affected.")
    exit(0)

except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("WARNING: Column extractors already exists, no need to add.")
        print("If you still get error, check if it's from another cause.")
        exit(0)
    else:
        print("ERROR: Failed to add column: %s" % e)
        exit(1)
except Exception as e:
    print("ERROR: Unknown error: %s" % e)
    exit(1)
finally:
    conn.close()
