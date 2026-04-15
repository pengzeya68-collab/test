import sqlite3, sys
db_path = 'instance/testmaster.db'
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, title FROM learning_paths ORDER BY id')
    rows = c.fetchall()
    print('=== learning_paths ===')
    for r in rows:
        print(repr(r))
    c.execute('SELECT id, learning_path_id, type, title, status FROM learning_path_items ORDER BY id')
    rows2 = c.fetchall()
    print('=== learning_path_items ===')
    for r in rows2:
        print(repr(r))
    c.execute('SELECT COUNT(*) FROM learning_path_items')
    print('total items:', c.fetchone()[0])
    conn.close()
except Exception as e:
    print('ERROR:', e, file=sys.stderr)
