import sys
sys.stdout = open(r'C:\Users\lenovo\Desktop\TestMasterProject\cleanup_out.txt', 'w', encoding='utf-8')
sys.stderr = sys.stdout

import os, sqlite3
os.chdir(r'C:\Users\lenovo\Desktop\TestMasterProject')

db = sqlite3.connect('instance/testmaster.db')
cur = db.cursor()

cur.execute('DELETE FROM learning_path_items WHERE status = "error" OR title = "" OR title IS NULL')
deleted_items = cur.rowcount
print('Items deleted:', deleted_items)

cur.execute('DELETE FROM learning_paths WHERE id NOT IN (SELECT DISTINCT learning_path_id FROM learning_path_items)')
deleted_lps = cur.rowcount
print('Empty learning_paths deleted:', deleted_lps)

db.commit()

cur.execute('SELECT COUNT(*) FROM learning_path_items')
print('Remaining items:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM learning_paths')
print('Remaining learning_paths:', cur.fetchone()[0])

db.close()
sys.stdout.close()
