#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

sys.stdout.reconfigure(encoding='utf-8')

from backend.app import create_app
from backend.extensions import db
from werkzeug.security import generate_password_hash

# 删除旧数据库
instance_path = os.path.join(project_root, 'instance')
db_path = os.path.join(instance_path, 'testmaster.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print("旧数据库已删除")

app = create_app()

with app.app_context():
    # 创建所有表
    db.create_all()
    print("✅ 所有表创建成功！")
    
    # 创建超级管理员
    from backend.models.models import AdminUser
    admin = AdminUser.query.filter_by(username='admin').first()
    if not admin:
        admin = AdminUser(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            name='超级管理员',
            email='admin@testmaster.com',
            role='super_admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
    print("✅ 超级管理员创建成功！")
    print("  账号：admin")
    print("  密码：admin123")
    
    # 创建测试用户
    from backend.models.models import User
    test_user = User(
        username='testuser',
        email='test@test.com',
        phone='13800138000',
        password_hash=generate_password_hash('password123'),
        is_active=True
    )
    db.session.add(test_user)
    db.session.commit()
    print("✅ 测试用户创建成功！")
    print("  账号：testuser")
    print("  密码：password123")

print("\n✅ 数据库初始化完成！")
