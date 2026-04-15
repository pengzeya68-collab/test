#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI兼容的数据库初始化脚本
替换旧的Flask初始化脚本(init_all.py)
"""
import asyncio
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash

from fastapi_backend.core.database import engine, Base, AsyncSessionLocal
from fastapi_backend.models.models import User


async def create_tables() -> None:
    """创建所有数据库表"""
    print("正在创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 所有表创建成功！")


async def create_admin_user() -> None:
    """创建超级管理员用户"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在管理员用户
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == 'admin'))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("⚠️  管理员用户已存在，跳过创建")
            return

        # 创建超级管理员
        admin = User(
            username='admin',
            email='admin@testmaster.com',
            phone='13800138000',
            password_hash=generate_password_hash('admin123'),
            is_active=True,
            is_admin=True,
            is_super_admin=True
        )

        session.add(admin)
        await session.commit()
        print("✅ 超级管理员创建成功！")
        print("  账号：admin")
        print("  密码：admin123")


async def create_test_user() -> None:
    """创建测试用户"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == 'testuser'))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("⚠️  测试用户已存在，跳过创建")
            return

        test_user = User(
            username='testuser',
            email='test@test.com',
            phone='13800138001',
            password_hash=generate_password_hash('password123'),
            is_active=True,
            is_admin=False,
            is_super_admin=False
        )

        session.add(test_user)
        await session.commit()
        print("✅ 测试用户创建成功！")
        print("  账号：testuser")
        print("  密码：password123")


async def backup_existing_database() -> None:
    """备份现有数据库文件"""
    instance_dir = os.path.join(project_root, 'instance')
    db_path = os.path.join(instance_dir, 'testmaster.db')
    backup_path = os.path.join(instance_dir, 'testmaster.db.backup')

    if os.path.exists(db_path):
        import shutil
        import datetime

        # 创建带时间戳的备份
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamped_backup = os.path.join(instance_dir, f'testmaster.db.backup_{timestamp}')

        try:
            shutil.copy2(db_path, timestamped_backup)
            print(f"✅ 数据库已备份到: {timestamped_backup}")
        except Exception as e:
            print(f"⚠️  数据库备份失败: {e}")
            # 尝试普通备份
            try:
                shutil.copy2(db_path, backup_path)
                print(f"✅ 数据库已备份到: {backup_path}")
            except Exception as e2:
                print(f"❌ 所有备份尝试都失败: {e2}")


async def main() -> None:
    """主初始化函数"""
    print("=" * 60)
    print("TestMaster FastAPI 数据库初始化")
    print("=" * 60)

    # 备份现有数据库
    await backup_existing_database()

    # 创建表
    await create_tables()

    # 创建用户
    await create_admin_user()
    await create_test_user()

    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n启动说明:")
    print("1. 启动后端: python -m uvicorn fastapi_backend.main:app --host 0.0.0.0 --port 5001 --reload")
    print("2. 或使用批处理文件: .\\start_all.bat")
    print("3. 访问API文档: http://localhost:5001/api/docs")
    print("4. 使用管理员登录: admin / admin123")


if __name__ == "__main__":
    # 设置Windows控制台编码为UTF-8
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ 初始化被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)