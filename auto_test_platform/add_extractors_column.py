#!/usr/bin/env python3
import sqlite3
import os

# 数据库文件路径 - 尝试 autotest.db (文件名没有下划线)
db_path = 'C:\\Users\\lenovo\\Desktop\\TestMasterProject\\auto_test_platform\\autotest.db'

print(f"Connecting to database: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查列是否已经存在
    cursor.execute("PRAGMA table_info(auto_test_cases)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'extractors' in column_names:
        print("Column 'extractors' already exists. No action needed.")
    else:
        # 添加 extractors 列，类型为 TEXT，默认值为空数组 JSON
        cursor.execute("ALTER TABLE auto_test_cases ADD COLUMN extractors TEXT DEFAULT '[]'")
        print("Successfully added column 'extractors' to table 'auto_test_cases'")

        # 更新所有现有行，设置为空数组
        cursor.execute("UPDATE auto_test_cases SET extractors = '[]' WHERE extractors IS NULL")
        print(f"Updated {cursor.rowcount} rows to set default value '[]'")

    # 提交更改
    conn.commit()

    # 再次验证
    cursor.execute("PRAGMA table_info(auto_test_cases)")
    columns = cursor.fetchall()
    print("\nCurrent table columns:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
    raise
finally:
    conn.close()

print("\nDone!")
