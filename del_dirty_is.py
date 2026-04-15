import sqlite3
conn = sqlite3.connect('instance/testmaster.db')
cur = conn.cursor()
# SQLite 不支持 DELETE ... ORDER BY LIMIT，需要用子查询
cur.execute('DELETE FROM interview_sessions WHERE id IN (SELECT id FROM interview_sessions ORDER BY id DESC LIMIT 2)')
print(f'DELETED: {cur.rowcount}')
conn.commit()
cur.execute('SELECT id, title, status FROM interview_sessions ORDER BY id DESC LIMIT 5')
for row in cur.fetchall():
    print(row)
conn.close()
