import sqlite3
conn = sqlite3.connect("instance/testmaster.db")
cur = conn.cursor()

print("=== learning_paths 表 ===")
cur.execute("SELECT id, title, item_count FROM learning_paths ORDER BY id")
for r in cur.fetchall():
    print(r)

print("\n=== exercises 总数 ===")
cur.execute("SELECT COUNT(*), COUNT(title) FROM exercises")
print(cur.fetchone())

print("\n=== exercises 样本（带title） ===")
cur.execute("SELECT id, learning_path_id, title, type, status FROM exercises WHERE title IS NOT NULL AND title != '' ORDER BY id LIMIT 20")
for r in cur.fetchall():
    print(r)

print("\n=== title 为空或NULL的 exercises ===")
cur.execute("SELECT id, learning_path_id, title, type FROM exercises WHERE title IS NULL OR title = ''")
nulls = cur.fetchall()
print(f"空title数量: {len(nulls)}")
for r in nulls[:20]:
    print(r)

conn.close()
