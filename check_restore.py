import sqlite3

conn = sqlite3.connect('c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform/auto_test.db')
cur = conn.cursor()

print("Current database state:")
print("api_cases:", cur.execute("SELECT COUNT(*) FROM api_cases").fetchone()[0])
print("api_groups:", cur.execute("SELECT COUNT(*) FROM api_groups").fetchone()[0])
print("environments:", cur.execute("SELECT COUNT(*) FROM environments").fetchone()[0])
print()
print("Sample cases (first 10):")
for row in cur.execute("SELECT id, name, method, url FROM api_cases LIMIT 10"):
    print(f"  ID:{row[0]} [{row[2]}] {row[1]} - {row[3][:50]}...")

conn.close()