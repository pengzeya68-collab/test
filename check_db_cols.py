import sqlite3

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db')
cursor = conn.cursor()

# 查看 auto_test_cases 表结构
cursor.execute("PRAGMA table_info(auto_test_cases)")
columns = cursor.fetchall()
print("auto_test_cases columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 查看 auto_test_groups 表结构
cursor.execute("PRAGMA table_info(auto_test_groups)")
columns = cursor.fetchall()
print("\nauto_test_groups columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 查一条数据看看
cursor.execute("SELECT * FROM auto_test_cases LIMIT 1")
row = cursor.fetchone()
if row:
    cursor.execute("PRAGMA table_info(auto_test_cases)")
    cols = [c[1] for c in cursor.fetchall()]
    print("\nSample row:")
    for i, val in enumerate(row):
        print(f"  {cols[i]}: {repr(val)[:100]}")

conn.close()