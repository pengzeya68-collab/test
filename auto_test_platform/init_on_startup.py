"""
启动时自动从Flask后端同步接口用例数据
并创建数据库备份
"""
import os
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Flask后端数据库
FLASK_DB = r"c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"
# FastAPI零代码平台数据库
FASTAPI_DB = r"c:/Users/lenovo/Desktop\TestMasterProject\auto_test_platform\auto_test.db"
# 备份目录
BACKUP_DIR = r"c:/Users/lenovo\Desktop\TestMasterProject\auto_test_platform\backups"


def backup_database():
    """备份FastAPI数据库"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"auto_test_backup_{timestamp}.db")

    if os.path.exists(FASTAPI_DB):
        shutil.copy2(FASTAPI_DB, backup_path)
        print(f"[BACKUP] Database backed up to: {backup_path}")
        return backup_path
    return None


def get_flask_interface_cases():
    """从Flask后端数据库提取接口用例"""
    if not os.path.exists(FLASK_DB):
        print(f"[WARNING] Flask database not found: {FLASK_DB}")
        return []

    try:
        conn = sqlite3.connect(FLASK_DB)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, folder_id, name, description, url, method, headers, body, body_type, is_public
            FROM interface_test_cases
            ORDER BY id
        """)
        cases = cursor.fetchall()

        cursor.execute("PRAGMA table_info(interface_test_cases)")
        columns = [row[1] for row in cursor.fetchall()]

        conn.close()

        return [dict(zip(columns, case)) for case in cases]
    except Exception as e:
        print(f"[ERROR] Failed to read Flask database: {e}")
        return []


def get_flask_folders():
    """从Flask后端数据库提取文件夹"""
    if not os.path.exists(FLASK_DB):
        return []

    try:
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
    except Exception as e:
        print(f"[ERROR] Failed to read Flask folders: {e}")
        return []


def should_sync():
    """
    检查是否需要同步
    如果FastAPI数据库为空或接近为空，则需要同步
    """
    if not os.path.exists(FASTAPI_DB):
        return True

    try:
        conn = sqlite3.connect(FASTAPI_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM api_cases")
        case_count = cursor.fetchone()[0]

        conn.close()

        # 如果用例少于50条，认为需要同步
        return case_count < 50
    except:
        return True


async def sync_from_flask():
    """
    从Flask后端同步数据到FastAPI平台
    返回同步的用例数量，失败返回False
    """
    if not should_sync():
        print("[SYNC] Data already exists, skipping sync")
        return False

    print("[SYNC] Starting data sync from Flask backend...")

    # 1. 备份现有数据库
    backup_path = backup_database()
    if not backup_path:
        print("[ERROR] Backup failed, aborting sync")
        return False

    # 2. 提取Flask数据
    flask_cases = get_flask_interface_cases()
    flask_folders = get_flask_folders()

    if not flask_cases:
        print("[WARNING] No interface cases found in Flask backend")
        return False

    print(f"[SYNC] Found {len(flask_cases)} cases and {len(flask_folders)} folders in Flask")

    # 3. 恢复到FastAPI数据库
    conn = sqlite3.connect(FASTAPI_DB)
    cursor = conn.cursor()

    # 创建默认分组
    cursor.execute("""
        INSERT INTO api_groups (id, name, parent_id, created_at)
        VALUES (NULL, 'Default Group', NULL, datetime('now'))
    """)
    default_group_id = cursor.lastrowid
    print(f"[SYNC] Created default group (ID: {default_group_id})")

    # 创建文件夹映射
    folder_id_map = {}
    for folder in flask_folders:
        name = folder.get('name') or 'Unnamed Group'
        parent_id = folder.get('parent_id')
        cursor.execute("""
            INSERT INTO api_groups (id, name, parent_id, created_at)
            VALUES (NULL, ?, ?, datetime('now'))
        """, (name, parent_id))
        folder_id_map[folder['id']] = cursor.lastrowid

    print(f"[SYNC] Created {len(folder_id_map)} folders")

    # 恢复接口用例
    cases_inserted = 0
    for case in flask_cases:
        folder_id = case.get('folder_id')
        group_id = folder_id_map.get(folder_id) if folder_id else default_group_id

        name = case.get('name') or 'Unnamed Case'
        method = case.get('method') or 'GET'
        url = case.get('url') or ''
        description = case.get('description') or ''

        headers = case.get('headers', '{}')
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except:
                headers = {}

        body = case.get('body', '')

        # 构建默认断言规则
        assert_rules = {
            "status_code": {"operator": "range", "expectedValue": "2xx/3xx"}
        }

        try:
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
        except Exception as e:
            print(f"[WARNING] Failed to insert case {name}: {e}")

    # 添加默认环境（如果不存在）
    cursor.execute("SELECT COUNT(*) FROM environments")
    env_count = cursor.fetchone()[0]
    if env_count == 0:
        cursor.execute("""
            INSERT INTO environments (id, env_name, base_url, variables, is_default, created_at)
            VALUES (NULL, 'Default Environment', 'http://localhost:5000', '{}', 1, datetime('now'))
        """)
        print("[SYNC] Created default environment")

    conn.commit()
    conn.close()

    print(f"[SYNC] Completed: {cases_inserted} cases restored")
    return cases_inserted


if __name__ == "__main__":
    # 可以直接运行此脚本进行手动同步
    import asyncio
    result = asyncio.run(sync_from_flask())
    print(f"Result: {result}")