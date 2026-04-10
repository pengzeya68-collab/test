# 初始化管理员账号脚本
from app import create_app
from models import AdminUser
from extensions import db
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 创建所有表（如果不存在）
    db.create_all()
    
    # 检查是否已经有管理员账号
    admin = AdminUser.query.filter_by(username='admin').first()
    
    if admin:
        print("管理员账号已存在，跳过创建")
        print(f"用户名：admin")
        print("密码：admin123")
    else:
        # 创建默认管理员账号（独立后台管理员表）
        admin_user = AdminUser(
            username='admin',
            name='超级管理员',
            email='admin@testmaster.com',
            password_hash=generate_password_hash('admin123'),
            role='super_admin',
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("默认管理员账号创建成功！")
        print("【重要】后台管理员账号是独立的，和前台用户完全分离")
        print("管理员用户名：admin")
        print("管理员密码：admin123")
        print("请登录后及时修改密码")

