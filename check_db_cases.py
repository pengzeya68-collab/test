import sqlite3
import json

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db')
cursor = conn.cursor()

# 查看 auto_test_cases 表结构和数据
cursor.execute("SELECT id, name, assert_rules FROM auto_test_cases LIMIT 5")
rows = cursor.fetchall()

print(f"Found {len(rows)} rows")
for row in rows:
    print(f"\nID: {row[0]}, Name: {row[1]}")
    print(f"  assert_rules raw: {repr(row[2])}")
    try:
        if row[2]:
            parsed = json.loads(row[2]) if isinstance(row[2], str) else row[2]
            print(f"  parsed: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
        else:
            print(f"  (null or empty)")
    except Exception as e:
        print(f"  parse error: {e}")

conn.close()