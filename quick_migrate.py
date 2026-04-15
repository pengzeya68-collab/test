
"""
快速数据库迁移脚本 - 为 api_cases 表添加 extractors 字段
"""
import sqlite3
import sys
from pathlib import Path

INSTANCE_DIR = Path(__file__).resolve().parent.parent / "instance"
DB_PATH = INSTANCE_DIR / "auto_test.db"

print(f"数据库路径: {DB_PATH}")

if not DB_PATH.exists():
    print(f"数据库文件不存在: {DB_PATH}")
    print("数据库将在首次启动后端时自动创建")
    sys.exit(0)

try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"当前 api_cases 表的列: {columns}")
    
    if 'extractors' not in columns:
        print("正在添加 extractors 字段...")
        cursor.execute("ALTER TABLE api_cases ADD COLUMN extractors TEXT")
        conn.commit()
        print("✅ extractors 字段添加成功！")
    else:
        print("✅ extractors 字段已存在，无需添加。")
        
    conn.close()
    print("\n数据库迁移完成！")
    
except Exception as e:
    print(f"\n❌ 迁移失败: {str(e)}")
    import traceback
    traceback.print_exc()

