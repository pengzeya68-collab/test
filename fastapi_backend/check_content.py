#!/usr/bin/env python3
"""查看课程内容和现有习题"""
import sqlite3

db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 课程内容样例 ===")
cursor.execute("""
    SELECT id, learning_path_id, title, content, knowledge_point 
    FROM lesson_sections 
    WHERE content IS NOT NULL AND content != ''
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"\n--- 章节ID {row[0]} (学习路径{row[1]}) ---")
    print(f"标题: {row[2]}")
    print(f"知识点: {row[4]}")
    content = row[3]
    # 打印前800字符
    print(f"内容: {content[:800] if content else 'Empty'}")

print("\n\n=== 现有习题检查 ===")
cursor.execute("SELECT COUNT(*) FROM exercises")
total = cursor.fetchone()[0]
print(f"总习题数: {total}")

# 检查每个学习路径有多少习题
cursor.execute("""
    SELECT learning_path_id, COUNT(*) as cnt 
    FROM exercises 
    GROUP BY learning_path_id 
    ORDER BY learning_path_id
""")
print("\n各学习路径习题数:")
for row in cursor.fetchall():
    print(f"  路径{row[0]}: {row[1]}题")

# 查看一道习题的详细内容
print("\n=== 习题详细样例 ===")
cursor.execute("""
    SELECT id, title, exercise_type, learning_path_id, description, solution 
    FROM exercises 
    LIMIT 2
""")
for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"类型: {row[2]}, 学习路径: {row[3]}")
    print(f"描述(选项):\n{row[4][:400] if row[4] else 'None'}")
    print(f"答案: {row[5]}")

conn.close()
print("\n✅ 完成！")
