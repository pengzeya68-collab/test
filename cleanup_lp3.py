import sqlite3, sys

conn = sqlite3.connect('instance/testmaster.db')
c = conn.cursor()

# Check for garbage titles (non-Chinese/English readable characters)
print('=== 检查所有 exercises 的 title ===')
c.execute('SELECT id, learning_path_id, title, exercise_type FROM exercises WHERE learning_path_id IS NOT NULL ORDER BY learning_path_id, id')
all_exercises = c.fetchall()

bad_ids = []
for r in all_exercises:
    eid, lpid, title, etype = r
    if not title:
        bad_ids.append(eid)
        print(f'BAD (empty): id={eid}, lpid={lpid}, title={repr(title)}')
    elif title in ('无标题', 'title', 'test', 'exam'):
        bad_ids.append(eid)
        print(f'BAD (suspicious): id={eid}, lpid={lpid}, title={repr(title)}')
    elif 'learning_path' in title.lower() or 'learningpath' in title.lower():
        bad_ids.append(eid)
        print(f'BAD (learning_path): id={eid}, lpid={lpid}, title={repr(title)}')
    elif title.startswith('<') or title.startswith('test'):
        bad_ids.append(eid)
        print(f'BAD (starts with < or test): id={eid}, lpid={lpid}, title={repr(title)}')
    else:
        print(f'OK: id={eid}, lpid={lpid}, title={repr(title)}, type={etype}')

print(f'\nTotal bad: {len(bad_ids)}')
print(f'Bad IDs: {bad_ids}')

# Now also check if there are learning paths with no exercises
print('\n=== 检查孤立的 learning_paths（无任何 exercise）===')
c.execute('''
    SELECT lp.id, lp.title, COUNT(e.id) as cnt
    FROM learning_paths lp
    LEFT JOIN exercises e ON e.learning_path_id = lp.id
    GROUP BY lp.id
    HAVING cnt = 0
''')
empty_lps = c.fetchall()
print(f'孤立 learning_paths: {empty_lps}')

# Delete bad exercises
if bad_ids:
    placeholders = ','.join('?' * len(bad_ids))
    c.execute(f'DELETE FROM exercises WHERE id IN ({placeholders})', bad_ids)
    conn.commit()
    print(f'\n已删除 {len(bad_ids)} 条垃圾 exercises')

# Delete empty learning paths
if empty_lps:
    lp_ids = [r[0] for r in empty_lps]
    placeholders = ','.join('?' * len(lp_ids))
    c.execute(f'DELETE FROM learning_paths WHERE id IN ({placeholders})', lp_ids)
    conn.commit()
    print(f'已删除 {len(empty_lps)} 个孤立 learning_paths')

conn.close()
print('\n清理完成！')
