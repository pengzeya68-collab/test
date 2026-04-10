#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建超级管理员账号
"""
from app import create_app
from extensions import db
from models import AdminUser
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    try:
        # 检查是否已有超级管理员
        super_admin = AdminUser.query.filter_by(role='super_admin').first()
        if super_admin:
            print(f"超级管理员已存在：{super_admin.username}")
            print(f"角色：{super_admin.role}")
        else:
            # 创建超级管理员账号
            super_admin = AdminUser(
                username='superadmin',
                password_hash=generate_password_hash('Super@123'),
                name='超级管理员',
                email='superadmin@testmaster.com',
                role='super_admin',
                is_active=True
            )
            
            db.session.add(super_admin)
            db.session.commit()
            
            print("✅ 超级管理员创建成功！")
            print("\n账号信息：")
            print("  用户名：superadmin")
            print("  密码：Super@123")
            print("  权限：只有超级管理员才能设置/取消其他用户的管理员权限")
        
        # 把现有admin的角色改成普通管理员
        admin_user = AdminUser.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.role = 'admin'
            db.session.commit()
            print("\n✅ 现有admin账号已设置为普通管理员")
    
    except Exception as e:
        print(f"❌ 创建失败：{str(e)}")
        db.session.rollback()
