import sqlite3, sys

conn = sqlite3.connect('instance/testmaster.db')
c = conn.cursor()

print('=== exercises (NULL/empty learning_path_id) ===')
c.execute("SELECT id, title, learning_path_id, exercise_type, difficulty FROM exercises WHERE learning_path_id IS NOT NULL ORDER BY learning_path_id, id")
for r in c.fetchall():
    print(r)

print()
print('=== total exercises with learning_path_id ===')
c.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id IS NOT NULL")
print(c.fetchone()[0])

print()
print('=== exercises with bad titles (NULL/empty/test/junk) ===')
c.execute("SELECT id, title, learning_path_id FROM exercises WHERE learning_path_id IS NOT NULL AND (title IS NULL OR title = '' OR title LIKE '%test%' OR title LIKE '%Test%' OR title LIKE '%<%' OR title LIKE 'exam_%' OR title LIKE 'learning_%' OR title LIKE '无标题' OR title LIKE '??%')")
print('bad exercises:', c.fetchall())

conn.close()
