#!/usr/bin/env python3
"""检查数据库中的课程内容和习题"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 学习路径 ===")
cursor.execute("SELECT id, title FROM learning_paths LIMIT 10")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n=== 课程内容样例 (lesson_sections) ===")
cursor.execute("""
    SELECT ls.id, ls.section_title, ls.lesson_id, l.title 
    FROM lesson_sections ls 
    JOIN lessons l ON ls.lesson_id = l.id 
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"Section {row[0]}: {row[1]} (课程: {row[3]})")

print("\n=== 课程内容详情样例 ===")
cursor.execute("""
    SELECT ls.id, ls.section_title, ls.content 
    FROM lesson_sections ls 
    WHERE ls.content IS NOT NULL AND ls.content != ''
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"\n--- Section {row[0]}: {row[1]} ---")
    content = row[2]
    # 只打印前500字符
    print(content[:500] if content else "Empty")

print("\n=== 现有习题样例 ===")
cursor.execute("""
    SELECT id, title, exercise_type, learning_path_id, description 
    FROM exercises 
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"\nID {row[0]}: {row[1]}")
    print(f"类型: {row[2]}, 学习路径: {row[3]}")
    print(f"描述: {row[4][:300] if row[4] else 'None'}")

conn.close()
print("\n完成！")
