"""
从Flask后端提取接口数据并恢复到FastAPI零代码平台
同时创建备份
"""
import sqlite3
import json
import os
import shutil
from datetime import datetime

# Flask后端数据库
FLASK_DB = r"c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
# FastAPI零代码平台数据库
FASTAPI_DB = r"c:/Users/lenovo/Desktop/TestMasterProject/instance/auto_test.db"
# 备份目录
BACKUP_DIR = r"c:/Users/lenovo/Desktop/TestMasterProject/fastapi_backend/autotest_data/backups"

def backup_database():
    """备份FastAPI数据库"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"auto_test_backup_{timestamp}.db")

    if os.path.exists(FASTAPI_DB):
        shutil.copy2(FASTAPI_DB, backup_path)
        print(f"[BACKUP] Database backed up to: {backup_path}")
        return backup_path
    else:
        print("[WARNING] FastAPI database file does not exist")
        return None

def get_flask_interface_cases():
    """从Flask后端数据库提取接口用例"""
    conn = sqlite3.connect(FLASK_DB)
    cursor = conn.cursor()

    # 获取所有接口用例
    cursor.execute("""
        SELECT id, user_id, folder_id, name, description, url, method, headers, body, body_type, is_public
        FROM interface_test_cases
        ORDER BY id
    """)
    cases = cursor.fetchall()

    # 获取列名
    cursor.execute("PRAGMA table_info(interface_test_cases)")
    columns = [row[1] for row in cursor.fetchall()]

    conn.close()

    return [dict(zip(columns, case)) for case in cases]

def get_flask_folders():
    """从Flask后端数据库提取文件夹"""
    conn = sqlite3.connect(FLASK_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, parent_id, name, description
        FROM interface_test_folders
        ORDER BY id
    """)
    folders = cursor.fetchall()

    cursor.execute("PRAGMA table_info(interface_test_folders)")
    columns = [row[1] for row in cursor.fetchall()]

    conn.close()

    return [dict(zip(columns, folder)) for folder in folders]

def restore_to_fastapi():
    """将Flask数据恢复到FastAPI零代码平台"""
    print("\n" + "="*60)
    print("Starting data restore")
    print("="*60)

    # 1. 先备份
    backup_path = backup_database()
    if not backup_path:
        print("[ERROR] Backup failed, cannot continue")
        return False

    # 2. 提取Flask数据
    print("\n[1/3] Extracting data from Flask backend...")
    flask_cases = get_flask_interface_cases()
    flask_folders = get_flask_folders()
    print(f"  - Found {len(flask_cases)} interface cases")
    print(f"  - Found {len(flask_folders)} folders")

    if not flask_cases:
        print("[ERROR] No interface cases in Flask backend")
        return False

    # 3. 恢复到FastAPI数据库
    print("\n[2/3] Restoring to FastAPI platform...")

    # 连接FastAPI数据库
    conn = sqlite3.connect(FASTAPI_DB)
    cursor = conn.cursor()

    # 恢复文件夹 (api_groups)
    # 首先创建一个默认分组，用于存放没有分组的用例
    cursor.execute("""
        INSERT INTO api_groups (id, name, parent_id, created_at)
        VALUES (NULL, '默认分组', NULL, datetime('now'))
    """)
    default_group_id = cursor.lastrowid
    print(f"  - Created default group (ID: {default_group_id})")

    folder_id_map = {}  # old_id -> new_id
    for folder in flask_folders:
        name = folder.get('name') or '未命名分组'
        parent_id = folder.get('parent_id')
        cursor.execute("""
            INSERT INTO api_groups (id, name, parent_id, created_at)
            VALUES (NULL, ?, ?, datetime('now'))
        """, (name, parent_id))
        folder_id_map[folder['id']] = cursor.lastrowid

    # 获取新插入的文件夹ID
    if flask_folders:
        cursor.execute("SELECT id, name FROM api_groups ORDER BY id")
        all_folders = cursor.fetchall()
        print(f"  - 已插入 {len(all_folders)} 个文件夹到 api_groups 表")

    # 恢复接口用例 (api_cases)
    # 先获取现有的最大ID
    cursor.execute("SELECT MAX(id) FROM api_cases")
    max_id = cursor.fetchone()[0] or 0

    cases_inserted = 0
    for case in flask_cases:
        max_id += 1
        headers = case.get('headers', '{}')
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except:
                headers = {}

        body = case.get('body', '')
        body_type = case.get('body_type', 'json')

        # 构建assert_rules (默认断言)
        assert_rules = {
            "status_code": {"operator": "range", "expectedValue": "2xx/3xx"}
        }

        # 处理可能的NULL值
        folder_id = case.get('folder_id')
        # 如果folder_id为空或者不在映射表中，使用默认分组
        group_id = folder_id_map.get(folder_id) if folder_id else default_group_id
        name = case.get('name') or '未命名用例'
        method = case.get('method') or 'GET'
        url = case.get('url') or ''
        description = case.get('description') or ''

        cursor.execute("""
            INSERT INTO api_cases (id, group_id, name, method, url, headers, payload, assert_rules, description, updated_at)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            group_id,
            name,
            method,
            url,
            json.dumps(headers, ensure_ascii=False),
            body,
            json.dumps(assert_rules, ensure_ascii=False),
            description
        ))
        cases_inserted += 1

    # 恢复环境变量 (environments)
    # 插入一个默认环境
    cursor.execute("""
        INSERT INTO environments (id, env_name, base_url, variables, is_default, created_at)
        VALUES (NULL, '默认环境', 'http://localhost:5001', '{}', 1, datetime('now'))
    """)

    conn.commit()

    # 验证结果
    cursor.execute("SELECT COUNT(*) FROM api_cases")
    total_cases = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM api_groups")
    total_groups = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM environments")
    total_envs = cursor.fetchone()[0]

    print(f"  - inserted {cases_inserted} cases into api_cases table")
    print(f"  - api_cases table now has {total_cases} records")
    print(f"  - api_groups table now has {total_groups} records")
    print(f"  - environments table now has {total_envs} records")

    conn.close()

    print("\n[3/3] Data restore complete!")
    print("="*60)
    print(f"SUCCESS: Restored {cases_inserted} interface cases")
    print(f"   Backup location: {backup_path}")
    print("="*60)

    return True

if __name__ == "__main__":
    restore_to_fastapi()