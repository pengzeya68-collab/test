import sqlite3

conn = sqlite3.connect('instance/testmaster.db')
c = conn.cursor()

print('=== 恢复后验证 ===')
c.execute('SELECT COUNT(*) FROM exercises WHERE learning_path_id IS NOT NULL')
total = c.fetchone()[0]
print(f'有 learning_path_id 的 exercises: {total} 条')

print('\n--- exercises 按 learning_path_id 分组 ---')
c.execute("""
    SELECT lp.id, lp.title, COUNT(e.id) as cnt
    FROM learning_paths lp
    LEFT JOIN exercises e ON e.learning_path_id = lp.id
    GROUP BY lp.id
    ORDER BY lp.id
""")
for r in c.fetchall():
    print(f'  LP id={r[0]}, title={repr(r[1])}, exercises={r[2]}')

print('\n--- posts 无标题数据 ---')
c.execute("SELECT id, title FROM posts WHERE title IS NULL OR title = '' OR title = '无标题'")
bad_posts = c.fetchall()
print(f'垃圾 posts: {len(bad_posts)} 条: {bad_posts}')

conn.close()
