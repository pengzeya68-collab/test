#!/usr/bin/env python3
"""查看刚插入的精品习题"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 学习路径1的精品习题样例 ===\n")

cursor.execute("""
    SELECT id, title, exercise_type, description, solution 
    FROM exercises 
    WHERE learning_path_id = 1
    LIMIT 10
""")

for i, row in enumerate(cursor.fetchall(), 1):
    print(f"{'=' * 70}")
    print(f"【习题{i}】ID: {row[0]}")
    print(f"类型: {row[2]}")
    print(f"题目: {row[1]}")
    print("\n选项/描述:")
    print(row[3])
    print(f"\n答案: {row[4]}")
    print()

conn.close()
print("\n完成！")
