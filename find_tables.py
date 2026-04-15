import sqlite3, sys

for db_path in ['instance/testmaster.db', 'instance/auto_test.db']:
    print(f'\n=== {db_path} ===')
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in c.fetchall()]
        print('Tables:', tables)
        conn.close()
    except Exception as e:
        print('ERROR:', e)
