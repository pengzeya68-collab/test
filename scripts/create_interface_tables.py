#!/usr/bin/env python3
import sys
import os
import json

# 添加项目路径
project_root = r'C:\Users\lenovo\Desktop\TestMasterProject'
sys.path.insert(0, project_root)

os.environ['SECRET_KEY'] = 'testmaster-dev-secret-key-2026'
os.environ['JWT_SECRET_KEY'] = 'testmaster-jwt-secret-key-2026'

from backend.app import create_app
from backend.extensions import db
from backend.models.models import InterfaceTestFolder, InterfaceTestEnvironment

app = create_app()

with app.app_context():
    # 创建新表
    db.create_all()
    print("Created all tables (including new interface test tables)")
    print("✅ 数据库表创建成功！")
    print("\n新表：")
    print("- interface_test_folders （文件夹）")
print("- interface_test_environments （环境）")
