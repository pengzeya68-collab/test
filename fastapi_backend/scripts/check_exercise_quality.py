"""
检查习题数据质量
"""
import sqlite3
import os

# 直接硬编码正确的数据库路径
DB_PATH = r"C:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print('=== 习题数据质量检查 ===\n')

# 1. 检查总数量
cursor.execute('SELECT COUNT(*) FROM exercises')
total = cursor.fetchone()[0]
print(f'1. 总习题数: {total}')

# 2. 检查各学习路径的习题数量
cursor.execute("""
SELECT lp.id, lp.title, COUNT(e.id) 
FROM learning_paths lp 
LEFT JOIN exercises e ON lp.id = e.learning_path_id 
GROUP BY lp.id 
ORDER BY lp.id
""")
print('\n2. 各学习路径习题分布:')
for row in cursor.fetchall():
    print(f'   LP{row[0]}: {row[2]} 道 - {row[1][:30]}')

# 3. 检查空的标题
cursor.execute("SELECT COUNT(*) FROM exercises WHERE title IS NULL OR title = ''")
empty_title = cursor.fetchone()[0]
print(f'\n3. 标题为空的习题: {empty_title}')

# 4. 检查空的描述
cursor.execute("SELECT COUNT(*) FROM exercises WHERE description IS NULL OR description = ''")
empty_desc = cursor.fetchone()[0]
print(f'   描述为空的习题: {empty_desc}')

# 5. 检查空的答案
cursor.execute("SELECT COUNT(*) FROM exercises WHERE solution IS NULL OR solution = ''")
empty_solution = cursor.fetchone()[0]
print(f'\n4. 答案为空的习题: {empty_solution}')

# 6. 检查重复的标题
cursor.execute("""
SELECT title, COUNT(*) as cnt 
FROM exercises 
GROUP BY title 
HAVING cnt > 1 
LIMIT 10
""")
duplicates = cursor.fetchall()
print(f'\n5. 标题重复的习题组数: {len(duplicates)}')
if duplicates:
    print('   前10组重复标题:')
    for title, cnt in duplicates[:10]:
        print(f'   - "{title[:40]}..." 重复 {cnt} 次')

# 7. 检查空的 category
cursor.execute("SELECT COUNT(*) FROM exercises WHERE category IS NULL OR category = ''")
bad_category = cursor.fetchone()[0]
print(f'\n6. category为空的习题: {bad_category}')

# 8. 检查习题类型分布
cursor.execute("""
SELECT exercise_type, COUNT(*) 
FROM exercises 
GROUP BY exercise_type
""")
print('\n7. 习题类型分布:')
for row in cursor.fetchall():
    print(f'   {row[0]}: {row[1]} 道')

# 9. 检查语言分布
cursor.execute("""
SELECT language, COUNT(*) 
FROM exercises 
GROUP BY language
""")
print('\n8. 语言分布:')
for row in cursor.fetchall():
    print(f'   {row[0]}: {row[1]} 道')

# 10. 检查难度分布
cursor.execute("""
SELECT difficulty, COUNT(*) 
FROM exercises 
GROUP BY difficulty
""")
print('\n9. 难度分布:')
for row in cursor.fetchall():
    print(f'   {row[0]}: {row[1]} 道')

conn.close()
print('\n=== 检查完成 ===')
