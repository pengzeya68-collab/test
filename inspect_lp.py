import sqlite3, sys, json

conn = sqlite3.connect('instance/testmaster.db')
c = conn.cursor()

# Check learning_paths schema and data
print('=== learning_paths ===')
c.execute("PRAGMA table_info(learning_paths)")
for r in c.fetchall():
    print('col:', r)
c.execute('SELECT id, title, description FROM learning_paths ORDER BY id')
for r in c.fetchall():
    print('row:', r)

print()
print('=== exercises (first 20) ===')
c.execute("PRAGMA table_info(exercises)")
for r in c.fetchall():
    print('col:', r)
c.execute('SELECT id, title, type, learning_path_id FROM exercises ORDER BY id LIMIT 30')
for r in c.fetchall():
    print('row:', r)

print()
print('=== progress (first 10) ===')
c.execute('SELECT id, user_id, type, item_id, status FROM progress LIMIT 10')
for r in c.fetchall():
    print('row:', r)

conn.close()
