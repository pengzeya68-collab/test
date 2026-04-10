#!/usr/bin/env python3
import sqlite3

# 尝试两个数据库文件
db_files = [
    'C:\\Users\\lenovo\\Desktop\\TestMasterProject\\auto_test_platform\\auto_test.db',
    'C:\\Users\\lenovo\\Desktop\\TestMasterProject\\auto_test_platform\\autotest.db'
]

for db_path in db_files:
    print(f"\n{'='*60}")
    print(f"Checking database: {db_path}")
    print(f"File exists: {__import__('os').path.exists(db_path)}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")

            # 显示表结构
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"    Columns:")
            for col in columns:
                print(f"      {col[1]}: {col[2]}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

print(f"\n{'='*60}")
