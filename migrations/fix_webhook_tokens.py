#!/usr/bin/env python3
"""
数据修复脚本：为所有没有 webhook_token 的现有场景生成 UUID Token
直接操作 SQLite 数据库，不启动 Flask app
"""

import sqlite3
import uuid
import os

# 数据库路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'instance', 'testmaster.db')

print("Connecting to database: %s" % db_path)

if not os.path.exists(db_path):
    print("ERROR: Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询所有 webhook_token 为空的记录
cursor.execute("""
    SELECT id, name FROM test_scenarios
    WHERE webhook_token IS NULL OR webhook_token = ''
""")
rows = cursor.fetchall()

if not rows:
    print("OK: No records need fixing, all scenarios already have webhook_token.")
    conn.close()
    exit(0)

print("Found %d records missing webhook_token" % len(rows))
print("Generating tokens...\n")

fixed_count = 0
for row_id, name in rows:
    token = str(uuid.uuid4())
    print("  ID %d: '%s' -> %s" % (row_id, name, token))
    cursor.execute("""
        UPDATE test_scenarios SET webhook_token = ? WHERE id = ?
    """, (token, row_id))
    fixed_count += 1

conn.commit()
conn.close()

print("\nDone! Fixed %d records." % fixed_count)
print("All scenarios now have webhook_token for CI/CD Webhook.")
