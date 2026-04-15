import os
os.chdir(r'C:\Users\lenovo\Desktop\TestMasterProject')
import sqlite3
db = sqlite3.connect('instance/testmaster.db')
cur = db.cursor()
cur.execute('SELECT id, learning_path_id, item_type, title, status FROM learning_path_items ORDER BY id')
rows = list(cur.fetchall())
with open('lp_out.txt', 'w', encoding='utf-8') as f:
    f.write('learning_path_items count: ' + str(len(rows)) + '\n')
    for r in rows:
        f.write(str(r) + '\n')
    f.write('\nlearning_paths:\n')
    cur.execute('SELECT id, title FROM learning_paths')
    for r in cur.fetchall():
        f.write(str(r) + '\n')
db.close()
