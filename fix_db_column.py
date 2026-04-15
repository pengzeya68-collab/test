
def fix_it():
    import sqlite3
    from pathlib import Path
    import sys
    import os

    # 确定当前工作目录
    current_dir = Path(__file__).resolve().parent
    INSTANCE_DIR = current_dir / "instance"
    DB_PATH = INSTANCE_DIR / "auto_test.db"

    print(f"数据库路径: {DB_PATH}")
    print(f"数据库存在: {DB_PATH.exists()}")

    if not DB_PATH.exists():
        print(f"在 {INSTANCE_DIR} 下未找到 auto_test.db")
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
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_it()

