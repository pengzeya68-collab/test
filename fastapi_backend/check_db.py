#!/usr/bin/env python3
"""检查数据库结构"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 所有数据表 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"\n📋 {table[0]}")
    # 查看每个表的字段
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

print("\n\n=== learning_paths 表数据 ===")
cursor.execute("SELECT id, title FROM learning_paths LIMIT 10")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n=== lesson_sections 表数据 ===")
cursor.execute("SELECT COUNT(*) FROM lesson_sections")
count = cursor.fetchone()[0]
print(f"总共有 {count} 个课程章节")

if count > 0:
    cursor.execute("SELECT id, section_title, content FROM lesson_sections LIMIT 3")
    for row in cursor.fetchall():
        print(f"\nID: {row[0]}")
        print(f"标题: {row[1]}")
        content = row[2] if row[2] else ""
        print(f"内容(前200字): {content[:200]}")

print("\n=== exercises 表数据 ===")
cursor.execute("SELECT COUNT(*) FROM exercises")
count = cursor.fetchone()[0]
print(f"总共有 {count} 道习题")

if count > 0:
    cursor.execute("SELECT id, title, exercise_type, learning_path_id FROM exercises LIMIT 5")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} ({row[2]}) - 路径{row[3]}")

conn.close()
print("\n✅ 完成！")
