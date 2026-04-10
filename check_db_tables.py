import sqlite3

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db')
cursor = conn.cursor()

# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# 查找包含 assert 关键字的表
for table in tables:
    name = table[0]
    cursor.execute(f"PRAGMA table_info({name})")
    columns = cursor.fetchall()
    col_names = [c[1] for c in columns]
    if 'assert' in str(col_names).lower():
        print(f"\nTable '{name}' has assert-related columns:")
        print(f"  Columns: {col_names}")
        cursor.execute(f"SELECT * FROM {name} LIMIT 2")
        rows = cursor.fetchall()
        print(f"  Sample data: {rows}")

conn.close()