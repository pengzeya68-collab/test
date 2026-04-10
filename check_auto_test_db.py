import sqlite3

db_path = r"c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform/auto_test.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite')]

print("=" * 60)
print("auto_test.db 数据库完整内容")
print("=" * 60)

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"\n表: {table} ({count} 条记录)")

    if count > 0:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"  列: {columns}")

        cursor.execute(f"SELECT * FROM {table} LIMIT 10")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  数据: {row}")

conn.close()