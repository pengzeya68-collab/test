"""
修复数据库中 JSON 字段的空字符串问题
SQLAlchemy JSON 类型要求必须是有效的 JSON 文本，空字符串 '' 会导致 JSONDecodeError
需要改为 NULL
"""
import sqlite3
import json

DB_PATH = 'c:/Users/lenovo/Desktop/TestMasterProject/auto_test_platform/auto_test.db'

def fix_json_fields():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查看api_cases表
    print("Checking api_cases table...")
    cursor.execute("SELECT id, headers, payload, assert_rules FROM api_cases")
    rows = cursor.fetchall()
    
    fixed = 0
    
    for row_id, headers, payload, assert_rules in rows:
        updated = False
        
        # 检查headers
        if headers == '':
            print(f"  Fixing id={row_id}: headers is empty string -> NULL")
            cursor.execute("UPDATE api_cases SET headers = NULL WHERE id = ?", (row_id,))
            updated = True
        
        # 检查payload
        if payload == '':
            print(f"  Fixing id={row_id}: payload is empty string -> NULL")
        # 注意：SQLite 中 Python None 对应 SQL NULL
            cursor.execute("UPDATE api_cases SET payload = NULL WHERE id = ?", (row_id,))
            updated = True
        
        # 检查assert_rules
        if assert_rules == '':
            print(f"  Fixing id={row_id}: assert_rules is empty string -> NULL")
            cursor.execute("UPDATE api_cases SET assert_rules = NULL WHERE id = ?", (row_id,))
            updated = True
        
        if updated:
            fixed += 1
    
    conn.commit()
    print(f"\nFixed {fixed} rows updated")
    
    # 验证修复
    print("\nVerifying...")
    cursor.execute("SELECT COUNT(*) FROM api_cases WHERE headers = '' OR payload = '' OR assert_rules = ''")
    remaining = cursor.fetchone()[0]
    print(f"Remaining empty string rows: {remaining}")
    
    conn.close()

if __name__ == "__main__":
    fix_json_fields()
