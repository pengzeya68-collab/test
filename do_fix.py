#!/usr/bin/env python3
import sqlite3
import os

db_path = 'instance/testmaster.db'
full_path = os.path.join(os.getcwd(), db_path)

print(f"数据库路径: {full_path}")

if not os.path.exists(full_path):
    print(f"❌ 数据库不存在: {full_path}")
    exit(1)

conn = sqlite3.connect(full_path)
cursor = conn.cursor()

print("\n=== 当前所有环境配置 ===")
cursor.execute('SELECT id, name, base_url FROM interface_test_environments')
for row in cursor.fetchall():
    print(f"  ID={row[0]}, 名称={row[1]}, base_url={row[2]}")

print("\n=== 开始替换 ===")
print("替换规则: :3000 -> :5000,  :5001 -> :5000")

# 替换环境配置中的端口
cursor.execute('UPDATE interface_test_environments SET base_url = REPLACE(base_url, ":3000", ":5000")')
changed_env1 = cursor.rowcount
cursor.execute('UPDATE interface_test_environments SET base_url = REPLACE(base_url, ":5001", ":5000")')
changed_env2 = cursor.rowcount

# 替换测试用例URL中的硬编码端口
cursor.execute('UPDATE interface_test_cases SET url = REPLACE(url, ":3000", ":5000")')
changed_case1 = cursor.rowcount
cursor.execute('UPDATE interface_test_cases SET url = REPLACE(url, ":5001", ":5000")')
changed_case2 = cursor.rowcount

conn.commit()

print(f"\n=== 替换完成 ===")
print(f"  环境配置: {changed_env1 + changed_env2} 处修改")
print(f"  测试用例: {changed_case1 + changed_case2} 处修改")

print("\n=== 修改后的环境配置 ===")
cursor.execute('SELECT id, name, base_url FROM interface_test_environments')
for row in cursor.fetchall():
    print(f"  ID={row[0]}, 名称={row[1]}, base_url={row[2]}")

conn.close()
print("\n✅ 成功！所有地址已经改成 localhost:5000 (你的Flask后端端口)")
print("请重启后端服务，然后重新测试！")
