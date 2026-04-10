#!/usr/bin/env python3
import sqlite3

AUTO_DB = 'c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform/auto_test.db'
conn = sqlite3.connect(AUTO_DB)
conn.text_factory = str
cursor = conn.cursor()

print('=== auto_test.db 所有表 ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for t in tables:
    print(f"  {t[0]}")

print()
for tbl in [t[0] for t in tables]:
    try:
        cursor.execute(f"PRAGMA table_info({tbl})")
        cols = [c[1] for c in cursor.fetchall()]
        print(f"{tbl}: {cols}")
    except Exception as e:
        print(f"{tbl}: error - {e}")

conn.close()
print('\n完成')