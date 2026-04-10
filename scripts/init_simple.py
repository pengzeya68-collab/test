#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    # 创建所有表
    db.create_all()
    print("✅ 所有表创建成功！")
    
    # 查询管理员
    from models import AdminUser
    admin = AdminUser.query.filter_by(username='admin').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = AdminUser(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            name='Admin',
            email='admin@testmaster.com',
            role='super_admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ 管理员创建成功！")
    else:
        print("✅ 管理员已存在！")

print("\n✅ 初始化完成！")
print("管理员账号：admin / admin123")
