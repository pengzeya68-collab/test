import sqlite3

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\auto_test_platform\auto_test.db')
cursor = conn.cursor()

# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in auto_test.db:", [t[0] for t in tables])

# 如果有表，查看结构
for table in tables:
    name = table[0]
    cursor.execute(f"PRAGMA table_info({name})")
    columns = cursor.fetchall()
    col_names = [c[1] for c in columns]
    print(f"\n{name}: {col_names}")

conn.close()