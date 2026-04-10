#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from extensions import db
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 创建所有表
    db.create_all()
    print("All tables created successfully!")
    
    # 创建超级管理员
    from models import AdminUser
    admin = AdminUser.query.filter_by(username='admin').first()
    if not admin:
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
        print("Super admin created successfully!")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("Super admin already exists!")
