import sqlite3
import os
from pathlib import Path

# 获取数据库文件路径
INSTANCE_DIR = Path(__file__).resolve().parent / "instance"
DB_FILE = INSTANCE_DIR / "auto_test.db"

print(f"Checking database at: {DB_FILE}")

if os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Current columns in api_cases: {columns}")
    
    if "params" not in columns:
        print("Adding params column...")
        try:
            cursor.execute("ALTER TABLE api_cases ADD COLUMN params TEXT")
            conn.commit()
            print("✅ Success: params column added")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("✅ params column already exists")
        
    # Verify
    cursor.execute("PRAGMA table_info(api_cases)")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"Final columns: {final_columns}")
    
    conn.close()
else:
    print(f"Database file not found: {DB_FILE}")

print("\nDone.")