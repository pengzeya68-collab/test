#!/usr/bin/env python3
"""验证生成的习题质量"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 验证习题质量 ===\n")

# 1. 检查总数量
cursor.execute("SELECT COUNT(*) FROM exercises")
total = cursor.fetchone()[0]
print(f"✅ 总习题数: {total}")

# 2. 检查每个学习路径的习题数
cursor.execute("""
    SELECT learning_path_id, COUNT(*) as cnt 
    FROM exercises 
    GROUP BY learning_path_id 
    ORDER BY learning_path_id
""")
print("\n📊 各学习路径习题数:")
for row in cursor.fetchall():
    status = "✅" if row[1] >= 100 else "⚠️"
    print(f"  {status} 路径{row[0]}: {row[1]}题")

# 3. 检查选项是否完整（应该有A. B. C. D.）
print("\n🔍 检查选项完整性...")
cursor.execute("""
    SELECT id, title, description, exercise_type 
    FROM exercises 
    WHERE exercise_type IN ('single_choice', 'multiple_choice')
    LIMIT 20
""")
incomplete_count = 0
for row in cursor.fetchall():
    desc = row[2] if row[2] else ""
    has_a = "A." in desc or "A." in desc
    has_b = "B." in desc
    has_c = "C." in desc
    has_d = "D." in desc

    if not (has_a and has_b and has_c and has_d):
        incomplete_count += 1
        if incomplete_count <= 3:  # 只打印前3个不完整的
            print(f"  ⚠️  ID {row[0]}: 选项不完整")
            print(f"     标题: {row[1]}")
            print(f"     描述前200字: {desc[:200]}")

if incomplete_count == 0:
    print("  ✅ 所有习题选项完整！")
else:
    print(f"  ⚠️  检查了20道，其中 {incomplete_count} 道选项不完整")

# 4. 查看几道完整的习题样例
print("\n\n=== 习题样例 ===")
cursor.execute("""
    SELECT id, title, exercise_type, learning_path_id, description, solution 
    FROM exercises 
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"\n{'=' * 70}")
    print(f"ID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"类型: {row[2]}")
    print(f"学习路径: {row[3]}")
    print("\n描述/选项:")
    print(row[4])
    print(f"\n答案: {row[5]}")

# 5. 更新 learning_paths 的 exercise_count
print("\n\n=== 更新学习路径的习题数 ===")
cursor.execute("""
    SELECT id FROM learning_paths
""")
paths = cursor.fetchall()

for (path_id,) in paths:
    cursor.execute(
        "SELECT COUNT(*) FROM exercises WHERE learning_path_id = ?", (path_id,)
    )
    count = cursor.fetchone()[0]
    cursor.execute(
        "UPDATE learning_paths SET exercise_count = ? WHERE id = ?", (count, path_id)
    )
    print(f"  路径{path_id}: {count}题")

conn.commit()
print("\n✅ exercise_count 已更新！")

conn.close()
print("\n🎉 验证完成！")
