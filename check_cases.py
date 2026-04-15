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
    
    # 查询 api_cases 表的结构
    print("\n=== Table structure ===")
    cursor.execute("PRAGMA table_info(api_cases)")
    columns = cursor.fetchall()
    for column in columns:
        print(f"{column[1]}: {column[2]}")
    
    # 查询 api_cases 表中的数据
    print("\n=== Cases data ===")
    cursor.execute("SELECT id, name, method, url, group_id FROM api_cases")
    cases = cursor.fetchall()
    print(f"Total cases: {len(cases)}")
    for case in cases:
        print(f"ID: {case[0]}, Name: {case[1]}, Method: {case[2]}, URL: {case[3]}, Group ID: {case[4]}")
    
    # 查询 api_groups 表中的数据
    print("\n=== Groups data ===")
    cursor.execute("SELECT id, name, parent_id FROM api_groups")
    groups = cursor.fetchall()
    print(f"Total groups: {len(groups)}")
    for group in groups:
        print(f"ID: {group[0]}, Name: {group[1]}, Parent ID: {group[2]}")
    
    conn.close()
else:
    print(f"Database file not found: {DB_FILE}")

print("\nDone.")