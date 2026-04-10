#!/usr/bin/env python3
import sqlite3

db_path = 'C:\\Users\\lenovo\\Desktop\\TestMasterProject\\auto_test_platform\\auto_test.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%auto%' OR name LIKE '%test%';")
tables = cursor.fetchall()

print("Tables containing 'auto' or 'test':")
for t in tables:
    print(f"  - {t[0]}")

    cursor.execute(f"PRAGMA table_info({t[0]})")
    cols = cursor.fetchall()
    print(f"    Columns:")
    for c in cols:
        print(f"      {c[1]}: {c[2]}")

conn.close()
