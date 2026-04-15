import sqlite3

backup_path = 'instance/testmaster.db.backup_before_migration_20260412_161340'
main_db = 'instance/testmaster.db'

# Connect to backup
conn_backup = sqlite3.connect(backup_path)
conn_backup.row_factory = sqlite3.Row
c_backup = conn_backup.cursor()

# Get all exercises with learning_path_id from backup
c_backup.execute('SELECT * FROM exercises WHERE learning_path_id IS NOT NULL ORDER BY id')
backup_rows = c_backup.fetchall()
backup_ids = [r['id'] for r in backup_rows]
print(f'备份中 linked exercises: {len(backup_rows)} 条, IDs: {backup_ids[:10]}...{backup_ids[-5:]}')

# Get column names from backup
col_names = [desc[1] for desc in c_backup.execute('PRAGMA table_info(exercises)').fetchall()]
print(f'列名: {col_names}')

conn_backup.close()

# Connect to main db
conn_main = sqlite3.connect(main_db)
c_main = conn_main.cursor()

# Check what's currently in main db
c_main.execute('SELECT COUNT(*) FROM exercises WHERE learning_path_id IS NOT NULL')
current = c_main.fetchone()[0]
print(f'当前 main db linked exercises: {current}')

# Restore from backup
inserted = 0
skipped = 0
for row_dict in backup_rows:
    eid = row_dict['id']
    # Check if exists in main db
    c_main.execute('SELECT id FROM exercises WHERE id = ?', (eid,))
    if c_main.fetchone() is not None:
        skipped += 1
        continue
    # Insert from backup
    vals = [row_dict[col] for col in col_names]
    placeholders = ','.join(['?'] * len(col_names))
    try:
        c_main.execute(f'INSERT INTO exercises ({",".join(col_names)}) VALUES ({placeholders})', vals)
        inserted += 1
    except Exception as e:
        print(f'Error inserting id={eid}: {e}')

conn_main.commit()

# Verify
c_main.execute('SELECT COUNT(*) FROM exercises WHERE learning_path_id IS NOT NULL')
final = c_main.fetchone()[0]
print(f'恢复后: {inserted} 条新插入, {skipped} 条已存在跳过, 总共 {final} 条 linked exercises')

# Show first few
c_main.execute('SELECT id, learning_path_id, title FROM exercises WHERE learning_path_id IS NOT NULL ORDER BY id LIMIT 5')
for r in c_main.fetchall():
    print(f'  id={r[0]}, lpid={r[1]}, title={repr(r[2])}')

conn_main.close()
print('\n恢复完成！')
