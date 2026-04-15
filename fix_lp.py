import sqlite3

main_db = 'instance/testmaster.db'
conn = sqlite3.connect(main_db)
c = conn.cursor()

# 1. 删除链接到不存在 learning_paths 的 exercises
print('=== 删除孤立 exercises ===')
c.execute("""
    DELETE FROM exercises
    WHERE learning_path_id IS NOT NULL
      AND learning_path_id NOT IN (SELECT id FROM learning_paths)
""")
deleted = c.rowcount
print(f'删除了 {deleted} 条孤立 exercises')

# 2. 验证当前状态
c.execute('SELECT COUNT(*) FROM exercises WHERE learning_path_id IS NOT NULL')
remaining = c.fetchone()[0]
print(f'剩余 linked exercises: {remaining} 条')

# 3. 查看当前 learning_paths 和 exercises 数量
print('\n=== 当前状态 ===')
c.execute('SELECT COUNT(*) FROM learning_paths')
lp_count = c.fetchone()[0]
print(f'learning_paths 数量: {lp_count}')

c.execute('SELECT COUNT(*) FROM exercises')
ex_count = c.fetchone()[0]
print(f'exercises 总数: {ex_count}')

# 4. 检查 posts 中的垃圾数据
c.execute("SELECT COUNT(*) FROM posts WHERE title IS NULL OR title = '' OR title = '无标题'")
bad_posts = c.fetchone()[0]
print(f'垃圾 posts: {bad_posts}')

conn.commit()
conn.close()
print('\n清理完成！')
