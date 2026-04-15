import sqlite3

conn = sqlite3.connect('instance/testmaster.db')
c = conn.cursor()

# Check posts table schema
print('--- posts schema ---')
c.execute("PRAGMA table_info(posts)")
for r in c.fetchall():
    print(r)

print('\n--- posts (前10条) ---')
c.execute('SELECT id, title FROM posts LIMIT 10')
for r in c.fetchall():
    print(r)

# Check all tables for "无标题"
print('\n--- 搜索 "无标题" ---')
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
for t in tables:
    try:
        c.execute(f"SELECT id, title FROM {t} WHERE title = '无标题' OR title LIKE '%<%' OR title LIKE '%test%' LIMIT 5")
        results = c.fetchall()
        if results:
            print(f'{t}: {results}')
    except Exception as e:
        pass

# Check exercises with NULL or suspicious titles
print('\n--- exercises 中 NULL/空 title ---')
c.execute('SELECT id, learning_path_id, title FROM exercises WHERE title IS NULL OR title = ""')
bad = c.fetchall()
if bad:
    for r in bad:
        print(f'BAD NULL: {r}')
else:
    print('无 NULL/空 title')

# Check learning_path_id=NULL but might still be linked somehow
print('\n--- 检查 learning_paths 自己的 title ---')
c.execute('SELECT id, title FROM learning_paths ORDER BY id')
for r in c.fetchall():
    print(f'LP: {r}')

conn.close()
