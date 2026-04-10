import sqlite3
import json

conn = sqlite3.connect(r'c:\Users\lenovo\Desktop\TestMasterProject\auto_test_platform\auto_test.db')
cursor = conn.cursor()

# 查 api_cases 数据
cursor.execute("SELECT id, group_id, name, method, assert_rules FROM api_cases LIMIT 10")
rows = cursor.fetchall()

print(f"Found {len(rows)} rows in api_cases")
for row in rows:
    print(f"\nID: {row[0]}, Group: {row[1]}, Name: {row[2]}, Method: {row[3]}")
    print(f"  assert_rules raw: {repr(row[4])}")
    if row[4]:
        try:
            parsed = json.loads(row[4]) if isinstance(row[4], str) else row[4]
            print(f"  parsed: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"  parse error: {e}")

conn.close()