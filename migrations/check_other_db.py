import sqlite3
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'instance', 'testmaster.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in instance/testmaster.db:")
for table in tables:
    print(f"  - {table[0]}")

# Check if test_scenarios exists and its columns
if any(table[0] == 'test_scenarios' for table in tables):
    print("\ntest_scenarios columns:")
    cursor.execute("PRAGMA table_info(test_scenarios)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]}: {col[2]}")

conn.close()
