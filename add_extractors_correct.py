#!/usr/bin/env python3
import sqlite3
import os

# 正确的数据库路径
db_path = 'C:\\Users\\lenovo\\Desktop\\TestMasterProject\\instance\\testmaster.db'

print(f"Connecting to database: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"\nAll tables: {tables}")

    if 'auto_test_cases' not in tables:
        print(f"\nERROR: Table 'auto_test_cases' not found in database!")
        exit(1)

    # 检查列是否已经存在
    cursor.execute("PRAGMA table_info(auto_test_cases)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print(f"\nCurrent columns in auto_test_cases:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    if 'extractors' in column_names:
        print("\nColumn 'extractors' already exists. No action needed.")
    else:
        # 添加 extractors 列，类型为 TEXT，默认值为空数组 JSON
        cursor.execute("ALTER TABLE auto_test_cases ADD COLUMN extractors TEXT DEFAULT '[]'")
        print("\nSuccessfully added column 'extractors' to table 'auto_test_cases'")

        # 更新所有现有行，设置为空数组
        cursor.execute("UPDATE auto_test_cases SET extractors = '[]' WHERE extractors IS NULL")
        print(f"Updated {cursor.rowcount} rows to set default value '[]'")

    # 提交更改
    conn.commit()

    # 再次验证
    cursor.execute("PRAGMA table_info(auto_test_cases)")
    columns = cursor.fetchall()
    print("\nAfter change - final columns:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

except Exception as e:
    print(f"\nError: {e}")
    conn.rollback()
    raise
finally:
    conn.close()

print("\nDone!")
