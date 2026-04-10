import sqlite3
import os

db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform/auto_test.db'
print(f'DB exists: {os.path.exists(db_path)}')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f'Tables: {[t[0] for t in tables]}')
    
    # 检查 api_cases
    cursor.execute('SELECT COUNT(*) FROM api_cases')
    print(f'api_cases count: {cursor.fetchone()[0]}')
    
    # 表结构
    cursor.execute('PRAGMA table_info(api_cases)')
    print('Table structure:')
    for col in cursor.fetchall():
        print(f'  {col[1]}: {col[2]}')
    
    # 测试查询
    print('\nTrying to query...')
    try:
        cursor.execute('SELECT * FROM api_cases LIMIT 1')
        row = cursor.fetchone()
        print(f'First row OK: {row}')
    except Exception as e:
        print(f'Query error: {e}')
    
    conn.close()
