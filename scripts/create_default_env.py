import sqlite3
import json
from datetime import datetime

AUTO_TEST_DB = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/auto_test.db'

conn = sqlite3.connect(AUTO_TEST_DB)
cursor = conn.cursor()

# 查看现有环境
cursor.execute('SELECT * FROM environments')
rows = cursor.fetchall()
print(f'现有环境数量: {len(rows)}')
for row in rows:
    print(row)

# 创建本地开发环境
now = datetime.now().isoformat()
cursor.execute('''
    INSERT INTO environments (env_name, base_url, variables, is_default, created_at)
    VALUES (?, ?, ?, ?, ?)
''', (
    '本地开发环境',
    'http://localhost:3000',
    json.dumps({
        'api_prefix': '/api',
        'base_url': 'http://localhost:3000'
    }, ensure_ascii=False),
    1,  # is_default
    now
))

env_id = cursor.lastrowid
print(f'\n创建环境成功: 本地开发环境 (ID: {env_id})')

conn.commit()
conn.close()