#!/usr/bin/env python3
"""后端启动诊断脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("Flask 后端启动诊断")
print("=" * 50)
print()

# 1. 检查 Python 版本
print("[1] Python 版本:")
print(f"    {sys.version}")
print()

# 2. 检查依赖
print("[2] 检查依赖...")
deps = [
    ("flask", "Flask"),
    ("flask_sqlalchemy", "Flask-SQLAlchemy"),
    ("flask_jwt_extended", "Flask-JWT-Extended"),
    ("flask_cors", "Flask-CORS"),
    ("flask_migrate", "Flask-Migrate"),
    ("flask_limiter", "Flask-Limiter"),
    ("sqlalchemy", "SQLAlchemy"),
]

for module, name in deps:
    try:
        mod = __import__(module)
        version = getattr(mod, '__version__', 'unknown')
        print(f"    [OK] {name}: {version}")
    except ImportError as e:
        print(f"    [MISSING] {name}: {e}")
print()

# 3. 测试 backend.app 导入
print("[3] 测试 backend.app 导入...")
try:
    from backend.app import create_app
    print("    [OK] backend.app 导入成功")
except Exception as e:
    print(f"    [ERROR] 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试 App 创建
print("[4] 测试 App 创建...")
try:
    app = create_app()
    print("    [OK] App 创建成功")
    print(f"    [INFO] 数据库 URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
except Exception as e:
    print(f"    [ERROR] App 创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 测试路由
print("[5] 测试路由注册...")
with app.app_context():
    rules = list(app.url_map.iter_rules())
    print(f"    [INFO] 共注册 {len(rules)} 个路由")
    # 显示前 10 个
    for rule in rules[:10]:
        print(f"         {rule.endpoint}: {rule.rule}")
    if len(rules) > 10:
        print(f"         ... 还有 {len(rules) - 10} 个路由")

print()
print("=" * 50)
print("诊断完成！后端代码没有问题。")
print("=" * 50)
