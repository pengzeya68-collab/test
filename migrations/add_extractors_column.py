"""
直接执行数据库迁移：为 api_cases 表添加 extractors 字段
"""
import sqlite3
import os
import json
from pathlib import Path

INSTANCE_DIR = Path(__file__).resolve().parent.parent / "fastapi_backend"
DB_PATH = INSTANCE_DIR / "testmaster.db"

def migrate():
    print(f"数据库路径: {DB_PATH}")
    print(f"数据库存在: {DB_PATH.exists()}")
    
    if not DB_PATH.exists():
        print("数据库文件不存在，将在首次启动后端时自动创建")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(api_cases)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 api_cases 表的列: {columns}")
        
        if 'extractors' not in columns:
            print("正在添加 extractors 字段...")
            cursor.execute("ALTER TABLE api_cases ADD COLUMN extractors TEXT")
            conn.commit()
            print("extractors 字段添加成功！")
        else:
            print("extractors 字段已存在，无需添加。")
            
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
