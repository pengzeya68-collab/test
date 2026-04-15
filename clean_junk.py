import sqlite3

conn = sqlite3.connect('instance/testmaster.db')
c = conn.cursor()

# 1. 检查 posts 表的"无标题"数据
print('=== posts 表中 title 异常的数据 ===')
c.execute("SELECT id, title FROM posts WHERE title IS NULL OR title = '' OR title = '无标题' OR title LIKE '%<%' OR title LIKE 'test%' OR title LIKE 'exam_%'")
bad_posts = c.fetchall()
print(f'垃圾 posts: {bad_posts}')

# 2. 检查 exercises 表的乱码/异常 title
print('\n=== exercises 表中 title 异常的数据 ===')
c.execute("""
    SELECT id, learning_path_id, title, exercise_type
    FROM exercises
    WHERE title IS NULL OR title = '' OR title = '无标题'
       OR title LIKE '%<%' OR title LIKE 'test%' OR title LIKE 'exam_%'
       OR title LIKE '%' || char(0) || '%'
       OR LENGTH(title) < 3
""")
bad_exercises = c.fetchall()
print(f'垃圾 exercises: {bad_exercises}')

# 3. 找出可能是乱码的 exercises（title 不含中文也不含英文常用词）
print('\n=== exercises 中可能是乱码的 title ===')
c.execute("SELECT id, learning_path_id, title FROM exercises WHERE learning_path_id IS NOT NULL")
for r in c.fetchall():
    eid, lpid, title = r
    # 检查是否包含中文字符
    has_cjk = any('\u4e00' <= ch <= '\u9fff' for ch in title)
    has_english = any(c.isalpha() for c in title)
    if not has_cjk and not has_english:
        print(f'乱码 exercise: id={eid}, lpid={lpid}, title={repr(title)}')

# 4. 删除垃圾 posts
if bad_posts:
    for r in bad_posts:
        c.execute('DELETE FROM posts WHERE id = ?', (r[0],))
    print(f'\n已删除 {len(bad_posts)} 条垃圾 posts')

# 5. 删除乱码/垃圾 exercises
bad_eids = [r[0] for r in bad_exercises]
if bad_eids:
    placeholders = ','.join('?' * len(bad_eids))
    c.execute(f'DELETE FROM exercises WHERE id IN ({placeholders})', bad_eids)
    print(f'已删除 {len(bad_eids)} 条垃圾 exercises: {bad_eids}')

conn.commit()
conn.close()
print('\n清理完成！')
