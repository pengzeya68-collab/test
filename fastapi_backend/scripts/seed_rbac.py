"""
RBAC 基础数据种子脚本（独立版）

直接连接 SQLite 数据库，不依赖项目配置。
用法：从项目根目录运行
  cd /c/Users/lenovo/Desktop/TestMasterProject
  .venv/Scripts/python.exe fastapi_backend/scripts/seed_rbac.py
"""
import sqlite3
import sys
import os
from datetime import datetime, timezone

# 无论在哪运行，都能找到项目根目录的 instance/testmaster.db
# __file__ = fastapi_backend/scripts/seed_rbac.py
# 项目根目录 = 3 层 parent
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "instance", "testmaster.db")
UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def seed_rbac():
    print(f"📊 数据库路径: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库不存在: {DB_PATH}")
        print(f"   当前目录: {os.getcwd()}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("📊 开始 RBAC 种子数据...")

    # ============ 1. 插入默认角色 ============
    roles = [
        ("admin", "管理员", "系统管理员，拥有所有权限", 1),
        ("tester", "测试员", "测试人员，拥有测试相关权限", 1),
        ("viewer", "观察者", "只读权限", 1),
    ]

    role_ids = {}
    for name, display_name, desc, is_system in roles:
        cursor.execute("SELECT id FROM roles WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            role_ids[name] = row[0]
            print(f"   ⚠️  角色已存在: {display_name} (id={row[0]})")
        else:
            cursor.execute(
                "INSERT INTO roles (name, display_name, description, is_system, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, display_name, desc, is_system, UTC_NOW, UTC_NOW)
            )
            conn.commit()
            rid = cursor.lastrowid
            role_ids[name] = rid
            print(f"   ✅ 创建角色: {display_name} (id={rid})")

    # ============ 2. 插入权限 ============
    permissions = [
        ("exercise:create", "创建习题", "创建新的习题", "exercise"),
        ("exercise:read", "查看习题", "查看习题详情", "exercise"),
        ("exercise:update", "编辑习题", "修改习题内容", "exercise"),
        ("exercise:delete", "删除习题", "删除习题", "exercise"),
        ("exercise:publish", "发布习题", "发布/下架习题", "exercise"),
        ("interview:create", "创建面试题", "创建面试题目", "interview"),
        ("interview:read", "查看面试题", "查看面试题详情", "interview"),
        ("interview:update", "编辑面试题", "修改面试题", "interview"),
        ("interview:delete", "删除面试题", "删除面试题", "interview"),
        ("exam:create", "创建考试", "创建考试", "exam"),
        ("exam:read", "查看考试", "查看考试详情", "exam"),
        ("exam:update", "编辑考试", "修改考试", "exam"),
        ("exam:delete", "删除考试", "删除考试", "exam"),
        ("exam:grade", "批改考试", "批改考试答卷", "exam"),
        ("user:manage", "管理用户", "创建/编辑/禁用用户", "user"),
        ("user:view", "查看用户", "查看用户信息", "user"),
        ("path:create", "创建学习路径", "创建学习路径", "path"),
        ("path:read", "查看学习路径", "查看学习路径", "path"),
        ("path:update", "编辑学习路径", "修改学习路径", "path"),
        ("path:delete", "删除学习路径", "删除学习路径", "path"),
        ("community:post:manage", "管理帖子", "置顶/加精/删除帖子", "community"),
        ("community:comment:manage", "管理评论", "删除评论", "community"),
        ("system:backup", "系统备份", "备份/恢复系统", "system"),
        ("system:config", "系统配置", "修改系统配置", "system"),
        ("system:log", "查看日志", "查看系统日志", "system"),
        ("system:ai_config", "AI配置", "配置AI模型", "system"),
        ("autotest:manage", "管理自动化测试", "管理接口测试用例", "autotest"),
        ("report:view", "查看报表", "查看测试报告", "report"),
        ("report:export", "导出报表", "导出测试报告", "report"),
    ]

    perm_ids = {}
    for code, name, desc, module in permissions:
        cursor.execute("SELECT id FROM permissions WHERE code = ?", (code,))
        row = cursor.fetchone()
        if row:
            perm_ids[code] = row[0]
        else:
            cursor.execute(
                "INSERT INTO permissions (code, name, description, module, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (code, name, desc, module, UTC_NOW)
            )
            conn.commit()
            pid = cursor.lastrowid
            perm_ids[code] = pid

    print(f"   ✅ 权限数据就绪（共 {len(permissions)} 个）")

    # ============ 3. 为角色分配权限 ============
    admin_perm_codes = list(perm_ids.keys())

    tester_perm_codes = [
        "exercise:create", "exercise:read", "exercise:update",
        "exercise:delete", "exercise:publish",
        "interview:create", "interview:read", "interview:update", "interview:delete",
        "exam:create", "exam:read", "exam:update", "exam:delete", "exam:grade",
        "path:create", "path:read", "path:update", "path:delete",
        "autotest:manage",
        "report:view", "report:export",
    ]

    viewer_perm_codes = [
        "exercise:read",
        "interview:read",
        "exam:read",
        "path:read",
        "report:view",
    ]

    role_perm_map = {
        "admin": admin_perm_codes,
        "tester": tester_perm_codes,
        "viewer": viewer_perm_codes,
    }

    for role_name, perm_codes in role_perm_map.items():
        role_id = role_ids.get(role_name)
        if not role_id:
            print(f"   ⚠️  角色不存在: {role_name}")
            continue

        # 清空现有权限
        cursor.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
        conn.commit()

        # 插入权限
        for code in perm_codes:
            perm_id = perm_ids.get(code)
            if not perm_id:
                print(f"   ⚠️  权限不存在: {code}")
                continue
            cursor.execute(
                "INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (?, ?, ?)",
                (role_id, perm_id, UTC_NOW)
            )
        conn.commit()
        print(f"   ✅ 为角色 [{role_name}] 分配了 {len(perm_codes)} 个权限")

    # ============ 4. 迁移现有 admin 用户 ============
    admin_role_id = role_ids.get("admin")
    if admin_role_id:
        cursor.execute(
            "UPDATE users SET role_id = ? WHERE is_admin = 1 AND role_id IS NULL",
            (admin_role_id,)
        )
        count = cursor.rowcount
        conn.commit()
        print(f"   ✅ 迁移了 {count} 个现有 admin 用户到 admin 角色")

    conn.close()
    print("\n🎉 RBAC 种子数据完成！")


if __name__ == "__main__":
    seed_rbac()
