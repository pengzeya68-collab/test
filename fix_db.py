import sqlite3
import sys

DB_PATH = r"c:\Users\lenovo\Desktop\TestMasterProject\fastapi_backend\testmaster.db"

print(f"数据库路径: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    print("检查 api_cases 表结构...")
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前列: {columns}")
    
    if 'extractors' not in columns:
        print("正在添加 extractors 字段...")
        cursor.execute("ALTER TABLE api_cases ADD COLUMN extractors TEXT")
        conn.commit()
        print("✅ extractors 字段添加成功！")
    else:
        print("✅ extractors 字段已存在！")
        
    print("\n验证修改...")
    cursor.execute("PRAGMA table_info(api_cases)")
    new_columns = [col[1] for col in cursor.fetchall()]
    print(f"新列: {new_columns}")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

print("\n修复完成！")
