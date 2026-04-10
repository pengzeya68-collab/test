"""
接口测试数据 → 自动化测试接口库 数据迁移脚本
将『在线接口测试』模块中所有已创建的接口用例完整迁移到『自动化测试』接口库中
保持数据结构完全一致，确保导入后可以直接执行

迁移逻辑:
1. 按用户分组迁移：每个用户在自动化测试分组中创建一个默认分组 "从接口测试导入"
2. 逐个复制接口用例，所有字段一一对应
3. JSON字段保持原样（两者格式完全相同，不需要转换）
4. 创建者ID保持不变，时间戳保持不变
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models.models import (
    InterfaceTestCase, InterfaceTestFolder,
    AutoTestCase, AutoTestGroup, User
)

def migrate_apis():
    app = create_app()

    # 解决Windows控制台编码问题
    import sys
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

    with app.app_context():
        print("=" * 60)
        print("TestMaster 接口测试数据迁移工具")
        print("来源: interface_test_cases -> 目标: auto_test_cases")
        print("=" * 60)

        # 统计信息
        total_users = 0
        total_folders_created = 0
        total_cases_migrated = 0
        total_skipped = 0

        # 获取所有有接口数据的用户
        # 先找出所有存在接口测试数据的用户
        source_cases = InterfaceTestCase.query.all()

        if len(source_cases) == 0:
            print("X 接口测试表中没有找到任何数据，迁移终止")
            return

        print(f"\n发现总共 {len(source_cases)} 条接口测试用例")

        # 按用户分组处理
        user_ids = list(set(case.user_id for case in source_cases))

        for user_id in user_ids:
            total_users += 1
            user = User.query.get(user_id)

            if not user:
                print(f"! 用户ID {user_id} 不存在，跳过该用户")
                total_skipped += len([c for c in source_cases if c.user_id == user_id])
                continue

            username = user.username
            print(f"\n[*] 处理用户 [{username}] (ID: {user_id})")

            # 检查该用户是否已经有 "从接口测试导入" 分组
            existing_folder = AutoTestGroup.query.filter_by(
                user_id=user_id,
                name="从接口测试导入"
            ).first()

            if existing_folder:
                print(f"[OK] 已存在默认分组: '{existing_folder.name}' (ID: {existing_folder.id})")
                target_folder_id = existing_folder.id
            else:
                # 创建默认分组
                new_folder = AutoTestGroup(
                    user_id=user_id,
                    name="从接口测试导入",
                    description="从原『在线接口测试』模块迁移过来的接口集合",
                    parent_id=None
                )
                db.session.add(new_folder)
                db.session.commit()
                total_folders_created += 1
                target_folder_id = new_folder.id
                print(f"[OK] 创建默认分组: '从接口测试导入' (ID: {target_folder_id})")

            # 获取该用户所有接口用例
            user_cases = InterfaceTestCase.query.filter_by(user_id=user_id).all()
            print(f"[*] 开始迁移 {len(user_cases)} 个接口用例...")

            migrated = 0
            for source_case in user_cases:
                # 检查是否已经迁移过（避免重复迁移）
                # 通过 name + url + user_id 判断是否重复
                existing_case = AutoTestCase.query.filter_by(
                    user_id=user_id,
                    name=source_case.name,
                    url=source_case.url
                ).first()

                if existing_case:
                    print(f"  [!] '{source_case.name}' 已存在，跳过")
                    total_skipped += 1
                    continue

                # 创建新的自动化测试用例
                target_case = AutoTestCase(
                    user_id=source_case.user_id,
                    folder_id=target_folder_id,
                    name=source_case.name,
                    method=source_case.method,
                    url=source_case.url,
                    description=source_case.description,
                    headers=source_case.headers,  # JSON文本格式完全相同，直接复制
                    body=source_case.body,      # 请求体格式完全相同，直接复制
                    body_type=source_case.body_type or 'json',
                    created_at=source_case.created_at,  # 保持原始创建时间
                    updated_at=source_case.updated_at   # 保持原始更新时间
                )

                db.session.add(target_case)
                migrated += 1
                total_cases_migrated += 1

            db.session.commit()
            print(f"  [OK] 完成: 迁移 {migrated} 个用例")

        # 输出最终统计
        print("\n" + "=" * 60)
        print("[OK] 迁移完成！统计信息:")
        print(f"  - 处理用户数: {total_users}")
        print(f"  - 创建默认分组: {total_folders_created}")
        print(f"  - 成功迁移用例: {total_cases_migrated}")
        print(f"  - 跳过（已存在）: {total_skipped}")
        print("=" * 60)
        print("\n[*] 迁移后验证:")
        print("  1. 登录账号，进入 自动化测试 -> 接口库")
        print("  2. 在左侧分组树中找到 '从接口测试导入'")
print("  3. 所有接口都已在这里，可以直接点击运行")
print("=" * 60)


if __name__ == '__main__':
    try:
        migrate_apis()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
