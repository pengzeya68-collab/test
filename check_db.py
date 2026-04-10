import sqlite3

# Check testmaster.db for auto test related tables
print("=== testmaster.db ===")
conn = sqlite3.connect('c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(f"All Tables: {[t[0] for t in tables]}")

# Check for auto test related tables
auto_test_tables = [t[0] for t in tables if 'auto' in t[0].lower() or 'interface' in t[0].lower() or 'test' in t[0].lower()]
print(f"\nAuto test related tables: {auto_test_tables}")

for t in tables:
    if t[0] != 'sqlite_sequence':
        cur.execute(f'SELECT COUNT(*) FROM {t[0]}')
        count = cur.fetchone()[0]
        if count > 0 or 'auto' in t[0].lower() or 'interface' in t[0].lower():
            print(f"  {t[0]}: {count} rows")

conn.close()
