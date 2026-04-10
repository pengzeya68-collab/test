import sqlite3

conn = sqlite3.connect(r'C:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db')
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("=== 数据库表数据统计 ===\n")
print(f"{'表名':<30} {'行数':>6}")
print("-" * 40)

total_rows = 0
for (table_name,) in tables:
    if table_name.startswith('sqlite_'):
        continue
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"{table_name:<30} {count:>6}")
    total_rows += count

print("-" * 40)
print(f"{'总计':<30} {total_rows:>6}")
print()

# 再检查 auto_test.db
print("\n=== 自动化测试数据库 (auto_test.db) ===\n")
print(f"{'表名':<30} {'行数':>6}")
print("-" * 40)

conn2 = sqlite3.connect(r'C:\Users\lenovo\Desktop\TestMasterProject\auto_test_platform\auto_test.db')
cursor2 = conn2.cursor()
cursor2.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables2 = cursor2.fetchall()

total_rows2 = 0
for (table_name,) in tables2:
    if table_name.startswith('sqlite_'):
        continue
    cursor2.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor2.fetchone()[0]
    print(f"{table_name:<30} {count:>6}")
    total_rows2 += count

print("-" * 40)
print(f"{'总计':<30} {total_rows2:>6}")

conn.close()
conn2.close()
