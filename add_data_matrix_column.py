"""
手动添加 data_matrix 列到 auto_test_plans 表
解决: sqlite3.OperationalError: no such column: auto_test_plans.data_matrix
"""

import sqlite3
import os

# 数据库路径
project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'instance', 'testmaster.db')

print("Database path: " + db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(auto_test_plans)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'data_matrix' in column_names:
        print("[OK] data_matrix column already exists, no action needed")
    else:
        # 添加 data_matrix 列
        cursor.execute("ALTER TABLE auto_test_plans ADD COLUMN data_matrix TEXT")
        conn.commit()
        print("[OK] Successfully added data_matrix column to auto_test_plans table")

    # 同时检查 is_active 列是否存在（我们也添加了这个）
    if 'is_active' not in column_names:
        cursor.execute("ALTER TABLE auto_test_plans ADD COLUMN is_active BOOLEAN DEFAULT 1")
        conn.commit()
        print("[OK] Successfully added is_active column to auto_test_plans table")
    else:
        print("[OK] is_active column already exists")

    print("\n[DONE] Database update completed! Please restart backend server to take effect.")

except Exception as e:
    print("[ERROR] " + str(e))
    conn.rollback()
finally:
    conn.close()
