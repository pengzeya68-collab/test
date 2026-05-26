#!/usr/bin/env python3
"""快速检查生成的习题质量"""
import sqlite3

db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 习题质量检查 ===\n")

# 查看前5道题
cursor.execute("""
    SELECT id, title, exercise_type, description, solution 
    FROM exercises 
    LIMIT 5
""")

for row in cursor.fetchall():
    print("="*70)
    print(f"ID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"类型: {row[2]}")
    print(f"\n选项/描述:")
    print(row[3])
    print(f"\n答案: {row[4]}")
    print()

# 统计各类型数量
print("\n=== 习题类型统计 ===")
cursor.execute("""
    SELECT exercise_type, COUNT(*) 
    FROM exercises 
    GROUP BY exercise_type
""")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}道")

conn.close()
print("\n完成！")
