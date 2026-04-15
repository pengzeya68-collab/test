import sqlite3

conn = sqlite3.connect('instance/testmaster.db')
c = conn.cursor()

print('=== learning_paths ===')
c.execute('SELECT id, title FROM learning_paths ORDER BY id')
for row in c.fetchall():
    print(row)

print()
print('=== learning_path_items (所有) ===')
c.execute('SELECT id, learning_path_id, type, title, status FROM learning_path_items ORDER BY id')
for row in c.fetchall():
    print(row)

print()
print('=== 总数 ===')
c.execute('SELECT COUNT(*) FROM learning_path_items')
print('items 总数:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM learning_path_items WHERE title IS NULL OR title = '' OR title = '无标题' OR title LIKE '%<%' OR title LIKE 'learning_%' OR title LIKE 'test%' OR title LIKE 'exam_%'")
print('疑似垃圾 title 数:', c.fetchone()[0])
conn.close()
