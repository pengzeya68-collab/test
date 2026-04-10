#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建与习题库对应的学习路径
"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

sys.stdout.reconfigure(encoding='utf-8')

from backend.app import create_app
from backend.extensions import db
from backend.models.models import LearningPath, User
from werkzeug.security import generate_password_hash

def create_learning_paths():
    app = create_app()
    with app.app_context():
        # 清空现有学习路径
        LearningPath.query.delete()
        db.session.commit()
        print("[OK] 已清空现有学习路径")
        
        # 获取或创建管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@testmaster.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        admin_id = admin.id
        
        paths = [
            {
                'name': '软件测试基础入门',
                'description': '''从零开始学习软件测试，掌握测试基础理论、测试类型、测试流程等核心知识。

本路径涵盖：
- 软件测试的定义和目的
- 软件生命周期
- 黑盒测试与白盒测试
- 测试用例设计基础
- 缺陷管理流程
- 测试计划编写

适合人群：
- 零基础想转行测试的人员
- 刚入行的测试新人
- 想了解测试的开发者

学习目标：
完成本路径学习后，你将掌握软件测试的基础知识，能够编写简单的测试用例，理解测试工作的基本流程。''',
                'stage': 1,
                'order': 1,
                'estimated_days': 7,
                'prerequisites': '无',
                'skills': '测试理论,测试流程,缺陷管理',
                'difficulty': 'easy'
            },
            {
                'name': '功能测试与用例设计',
                'description': '''深入学习功能测试方法和测试用例设计技术，掌握各种测试用例设计方法。

本路径涵盖：
- 等价类划分法
- 边界值分析法
- 判定表法
- 因果图法
- 场景法
- 错误推测法
- 登录、搜索、购物车等功能测试实战

适合人群：
- 有一定测试基础的人员
- 想提升用例设计能力的测试工程师
- 准备面试的求职者

学习目标：
能够熟练运用各种测试用例设计方法，为复杂功能设计全面的测试用例。''',
                'stage': 2,
                'order': 2,
                'estimated_days': 14,
                'prerequisites': '完成阶段1：软件测试基础入门',
                'skills': '用例设计,功能测试,测试方法',
                'difficulty': 'medium'
            },
            {
                'name': '接口测试实战',
                'description': '''掌握接口测试的核心技能，学习HTTP协议、RESTful API和接口测试工具的使用。

本路径涵盖：
- HTTP协议详解
- RESTful API设计规范
- 接口测试用例设计
- Postman工具使用
- JMeter接口测试
- 接口自动化测试框架搭建
- Token认证和签名机制

适合人群：
- 想学习接口测试的测试工程师
- 需要对接口进行测试的开发者
- 准备接口测试相关面试的人员

学习目标：
能够独立进行接口测试，设计接口测试用例，使用工具进行接口自动化测试。''',
                'stage': 3,
                'order': 3,
                'estimated_days': 14,
                'prerequisites': '完成阶段2：功能测试与用例设计',
                'skills': '接口测试,HTTP协议,Postman,JMeter',
                'difficulty': 'medium'
            },
            {
                'name': '自动化测试开发',
                'description': '''学习自动化测试框架和工具，掌握Web UI自动化和接口自动化测试开发。

本路径涵盖：
- Selenium WebDriver基础
- 元素定位方法
- 等待机制
- Page Object设计模式
- Pytest测试框架
- 接口自动化测试
- Appium移动端测试
- CI/CD集成

适合人群：
- 想学习自动化测试的测试工程师
- 想提升技术能力的测试人员
- 准备自动化测试面试的人员

学习目标：
能够搭建自动化测试框架，编写可维护的自动化测试脚本，实现持续集成。''',
                'stage': 4,
                'order': 4,
                'estimated_days': 21,
                'prerequisites': '完成阶段3：接口测试实战，具备Python基础',
                'skills': 'Selenium,Pytest,自动化框架,Page Object',
                'difficulty': 'hard'
            },
            {
                'name': '性能测试与优化',
                'description': '''学习性能测试方法和工具，掌握性能测试指标分析和瓶颈定位。

本路径涵盖：
- 性能测试基础概念
- 性能测试类型（负载、压力、稳定性）
- JMeter性能测试
- 性能指标分析
- 慢SQL排查与优化
- 性能瓶颈分析
- 系统调优方法

适合人群：
- 想学习性能测试的测试工程师
- 需要负责性能测试的人员
- 想深入了解系统性能的人员

学习目标：
能够设计性能测试方案，执行性能测试，分析测试结果，定位性能瓶颈。''',
                'stage': 5,
                'order': 5,
                'estimated_days': 21,
                'prerequisites': '完成阶段4：自动化测试开发',
                'skills': '性能测试,JMeter,SQL优化,瓶颈分析',
                'difficulty': 'hard'
            },
        ]
        
        for data in paths:
            path = LearningPath(
                title=data['name'],
                description=data['description'],
                stage=data['stage'],
                estimated_hours=data['estimated_days'] * 3,  # 每天3小时
                prerequisites=data['prerequisites'],
                language='通用',
                difficulty='beginner' if data['difficulty'] == 'easy' else ('intermediate' if data['difficulty'] == 'medium' else 'advanced'),
                is_public=True,
                user_id=admin_id
            )
            db.session.add(path)
        
        db.session.commit()
        
        print(f"[OK] 成功创建 {len(paths)} 个学习路径！")
        
        # 显示创建的学习路径
        print("\n[学习路径列表]")
        for path in LearningPath.query.all():
            print(f"  阶段{path.stage}: {path.title}")

if __name__ == '__main__':
    create_learning_paths()
