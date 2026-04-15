import sqlite3
conn = sqlite3.connect("instance/testmaster.db")
cur = conn.cursor()

print("=== learning_paths ===")
rows = cur.execute("SELECT id, title, exercise_count FROM learning_paths ORDER BY id").fetchall()
for r in rows:
    print(r)

print("\n=== exercises 总数 ===")
total, titled = cur.execute("SELECT COUNT(*), COUNT(title) FROM exercises").fetchone()
print(f"总数={total}, 有title={titled}")

print("\n=== exercises 有 title 的样本 ===")
rows = cur.execute('SELECT id, learning_path_id, title, exercise_type FROM exercises WHERE title IS NOT NULL AND title != "" ORDER BY id LIMIT 15').fetchall()
for r in rows:
    print(r)

print("\n=== exercises 无 title ===")
nulls = cur.execute('SELECT id, learning_path_id, title, exercise_type FROM exercises WHERE title IS NULL OR title = ""').fetchall()
print(f"空title数量: {len(nulls)}")
for r in nulls[:15]:
    print(r)

conn.close()
