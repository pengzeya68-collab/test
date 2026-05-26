"""
接口库测试数据种子脚本 - 用于 auto_test.db

用法:
  1. 本地运行: python scripts/seed_autotest_data.py
  2. 服务器运行: docker exec testmaster-backend python3 /app/scripts/seed_autotest_data.py
     或: docker cp scripts/seed_autotest_data.py testmaster-backend:/app/scripts/ && docker exec testmaster-backend python3 /app/scripts/seed_autotest_data.py
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timezone


def get_db_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db = os.path.join(project_root, "instance", "auto_test.db")
    if os.path.exists(db):
        return db
    return "/app/instance/auto_test.db"


def main():
    db_path = get_db_path()
    print(f"[INFO] 数据库: {db_path}")
    if not os.path.exists(db_path):
        print(f"[ERROR] 数据库不存在: {db_path}")
        sys.exit(1)

    db = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # ============================================================
    # 清空旧数据
    # ============================================================
    db.execute("DELETE FROM api_cases")
    db.execute("DELETE FROM api_groups")
    db.execute("DELETE FROM environments")
    print("[OK] 已清空旧数据")

    # ============================================================
    # 1. 环境 (表: environments | 列: id, env_name, base_url, variables, is_default, created_at)
    # ============================================================
    envs = [
        (1, "本地测试环境", "http://34.150.26.84:5001",
         {"env": "prod", "timeout": 30}, True),
    ]
    for e in envs:
        db.execute(
            "INSERT INTO environments (id, env_name, base_url, variables, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (*e, now),
        )
    print(f"[OK] 环境已创建: {len(envs)} 个")

    # ============================================================
    # 2. 分组 (表: api_groups | 列: id, name, parent_id, created_at)
    # ============================================================
    groups = [
        (1, "用户认证模块", None),
        (2, "题目管理模块", None),
        (3, "考试评测模块", None),
        (4, "系统管理模块", None),
        (5, "社区互动模块", None),
    ]
    for g in groups:
        db.execute(
            "INSERT INTO api_groups (id, name, parent_id, created_at) VALUES (?, ?, ?, ?)",
            (*g, now),
        )
    print(f"[OK] 分组已创建: {len(groups)} 个")

    # ============================================================
    # 3. 用例 (表: api_cases | 列: id, group_id, name, method, url,
    #    headers(JSON), params(JSON), body_type, content_type,
    #    payload(JSON), assert_rules(JSON), extractors(JSON), description, updated_at)
    # ============================================================
    cases = [
        (1, 1, "用户登录", "POST", "/api/v1/auth/login",
         {"Content-Type": "application/json"}, None,
         "raw", "application/json",
         {"username": "admin", "password": "admin123456"},
         None, None, "正常登录接口"),
        (2, 1, "用户注册", "POST", "/api/v1/auth/register",
         {"Content-Type": "application/json"}, None,
         "raw", "application/json",
         {"username": "newuser", "password": "123456", "email": "new@test.com"},
         None, None, "注册新用户"),
        (3, 1, "获取当前用户信息", "GET", "/api/v1/auth/me",
         {"Authorization": "Bearer {{token}}"}, None,
         "none", "", None, None, None, "需携带Token"),
        (4, 1, "未读通知数", "GET", "/api/v1/notifications/unread-count",
         {"Authorization": "Bearer {{token}}"}, None,
         "none", "", None, None, None, "获取通知数量"),

        (5, 2, "题目列表(分页)", "GET", "/api/v1/exercises?page=1&size=10",
         {"Authorization": "Bearer {{token}}"}, None,
         "none", "", None, None, None, "分页获取题目"),
        (6, 2, "题目详情", "GET", "/api/v1/exercises/1",
         {"Authorization": "Bearer {{token}}"}, None,
         "none", "", None, None, None, "按ID获取题目"),
        (7, 2, "搜索题目", "GET", "/api/v1/exercises/search?keyword=python",
         {"Authorization": "Bearer {{token}}"}, None,
         "none", "", None, None, None, "关键字搜索题目"),

        (8, 3, "考试列表", "GET", "/api/v1/exams",
         {"Authorization": "Bearer {{token}}"}, None,
         "none", "", None, None, None, "获取所有考试"),
        (9, 3, "提交考试答案", "POST", "/api/v1/exams/1/submit",
         {"Content-Type": "application/json", "Authorization": "Bearer {{token}}"},
         None, "raw", "application/json",
         {"answers": [{"question_id": 1, "answer": "A"}]},
         None, None, "提交考试作答"),

        (10, 4, "健康检查", "GET", "/api/health",
         None, None, "none", "",
         None, None, None, "无需认证"),
        (11, 4, "备份列表(管理员)", "GET", "/api/v1/admin/backups",
         {"Authorization": "Bearer {{admin_token}}"}, None,
         "none", "", None, None, None, "需管理员权限"),
        (12, 4, "创建备份(管理员)", "POST", "/api/v1/admin/backups",
         {"Content-Type": "application/json", "Authorization": "Bearer {{admin_token}}"},
         None, "raw", "application/json",
         {}, None, None, "创建数据库备份"),

        (13, 5, "社区帖子列表", "GET", "/api/v1/community/posts?page=1",
         {"Authorization": "Bearer {{token}}"}, None,
         "none", "", None, None, None, "分页获取帖子"),
        (14, 5, "发布帖子", "POST", "/api/v1/community/posts",
         {"Content-Type": "application/json", "Authorization": "Bearer {{token}}"},
         None, "raw", "application/json",
         {"title": "测试帖子", "content": "这是一条测试内容"},
         None, None, "发帖测试"),
        (15, 5, "排行榜", "GET", "/api/v1/leaderboard?type=score",
         None, None, "none", "",
         None, None, None, "积分排行"),
    ]

    for c in cases:
        db.execute("""INSERT INTO api_cases 
            (id, group_id, name, method, url, headers, params, body_type, 
             content_type, payload, assert_rules, extractors, description, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*c, now))
    print(f"[OK] 用例已创建: {len(cases)} 个")

    db.commit()

    # ============================================================
    # 验证
    # ============================================================
    print("\n" + "=" * 50)
    print("[验证] environments 表:")
    rows = db.execute("SELECT id, env_name, base_url, is_default FROM environments").fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]} | {r[2]} | default={r[3]}")

    print(f"\n[验证] api_groups: {db.execute('SELECT COUNT(*) FROM api_groups').fetchone()[0]} 个")
    print(f"[验证] api_cases:  {db.execute('SELECT COUNT(*) FROM api_cases').fetchone()[0]} 个")

    sample = db.execute(
        "SELECT name, method, url, body_type, content_type FROM api_cases WHERE id=1"
    ).fetchone()
    print(f"\n[示例] {sample[0]} | {sample[1]} | {sample[2]} | body={sample[3]} | ct={sample[4]}")

    db.close()
    print("\n[DONE] 导入完成! 刷新接口库页面，选择环境后点击执行即可。")


if __name__ == "__main__":
    main()
