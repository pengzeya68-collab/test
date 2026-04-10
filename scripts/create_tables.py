#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新创建所有表
"""
from app import create_app
from extensions import db
import os

# 删除旧数据库
if os.path.exists('testmaster.db'):
    os.remove('testmaster.db')
    print("旧数据库已删除")

app = create_app()

with app.app_context():
    # 创建所有表
    db.create_all()
    print("✅ 所有表创建成功！")
    
    # 创建超级管理员账号
    from models import AdminUser
    from werkzeug.security import generate_password_hash
    
    super_admin = AdminUser(
        username='admin',
        password_hash=generate_password_hash('admin123'),
        name='超级管理员',
        email='admin@testmaster.com',
        role='super_admin',
        is_active=True
    )
    
    db.session.add(super_admin)
    db.session.commit()
    print("✅ 超级管理员账号创建成功！")
    print("  用户名：admin")
    print("  密码：admin123")
