import sqlite3

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\auto_test_platform\auto_test.db')
cursor = conn.cursor()

# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# 检查 auto_test_cases 表结构
cursor.execute("PRAGMA table_info(auto_test_cases)")
columns = cursor.fetchall()
print("\nauto_test_cases columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 查数据
cursor.execute("SELECT id, name, assert_rules FROM auto_test_cases LIMIT 5")
rows = cursor.fetchall()
print(f"\nFound {len(rows)} rows in auto_test_cases")
for row in rows:
    print(f"\nID: {row[0]}, Name: {row[1]}")
    print(f"  assert_rules: {repr(row[2])}")

conn.close()