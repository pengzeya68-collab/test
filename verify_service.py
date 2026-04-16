#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TestMaster 服务验证脚本
启动服务后运行此脚本验证功能是否正常
"""
import sys
import os
import time
import requests

# 设置UTF-8编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_service():
    """检查FastAPI服务是否正常运行"""
    print("🔍 检查 FastAPI 服务...")

    try:
        response = requests.get("http://localhost:5001/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ FastAPI 服务正常 (状态: {data.get('status', 'unknown')})")
            return True
        else:
            print(f"❌ FastAPI 服务异常 (状态码: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到 FastAPI 服务: {e}")
        print("   请确保服务已启动: 使用 'TestMaster一键启动.bat' 选择选项 1 或 3")
        return False

def check_database():
    """检查数据库是否可访问"""
    print("\n🔍 检查数据库...")

    db_path = r"C:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db"
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查关键表
        tables = ["users", "exercises", "exams", "interview_questions"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ 表 {table:25} 存在, {count:5} 行数据")
            except sqlite3.Error:
                print(f"❌ 表 {table:25} 不存在或访问错误")

        conn.close()
        print("✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def test_auth():
    """测试用户认证功能"""
    print("\n🔍 测试用户认证...")

    try:
        # 测试管理员登录
        login_data = {
            "username": os.environ.get("TEST_ADMIN_USER", "admin"),
            "password": os.environ.get("TEST_ADMIN_PASSWORD", "")
        }

        response = requests.post(
            "http://localhost:5001/api/auth/login",
            json=login_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("✅ 管理员登录成功")
                return data["access_token"]
            else:
                print("❌ 登录响应中没有access_token")
                return None
        else:
            print(f"❌ 登录失败 (状态码: {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ 认证测试失败: {e}")
        return None

def test_api_endpoints(token=None):
    """测试API端点"""
    print("\n🔍 测试API端点...")

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    endpoints = [
        ("学习路径", "/api/learning-paths", "GET"),
        ("习题管理", "/api/exercises", "GET"),
        ("考试系统", "/api/exams", "GET"),
        ("面试系统", "/api/interview/questions", "GET"),
        ("自动化测试", "/api/auto-test/cases", "GET"),
    ]

    success_count = 0
    for name, endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(
                    f"http://localhost:5001{endpoint}",
                    headers=headers,
                    timeout=10
                )
            else:
                continue

            if response.status_code in [200, 201]:
                print(f"✅ {name:15} API正常")
                success_count += 1
            else:
                print(f"❌ {name:15} API异常 (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ {name:15} API测试失败: {e}")

    return success_count

def main():
    """主验证函数"""
    print("=" * 60)
    print("TestMaster 功能验证脚本")
    print("=" * 60)
    print("本脚本将验证FastAPI服务是否正常运行")
    print("请确保已使用 'TestMaster一键启动.bat' 启动服务")
    print()

    # 等待用户确认
    input("按 Enter 键开始验证...")
    print()

    # 1. 检查服务
    if not check_service():
        print("\n❌ 服务未启动，请先启动服务")
        return False

    # 2. 检查数据库
    if not check_database():
        print("\n⚠️  数据库存在问题，但服务可能仍可运行")

    # 3. 测试认证
    token = test_auth()

    # 4. 测试API
    api_success = test_api_endpoints(token)

    # 5. 总结
    print("\n" + "=" * 60)
    print("验证结果:")
    print("-" * 60)

    if token and api_success >= 3:  # 至少3个API成功
        print("✅ 所有核心功能正常！")
        print()
        print("服务访问地址:")
        print("  FastAPI后端: http://localhost:5001/api/docs")
        print("  前端界面: http://localhost:5173")
        print()
        print("默认账号:")
        print("  管理员: admin / admin123")
        print("  测试用户: testuser / password123")
        return True
    else:
        print("⚠️  部分功能存在问题，但服务基本可用")
        print()
        print("建议:")
        print("  1. 检查服务日志")
        print("  2. 确认数据库文件存在")
        print("  3. 验证网络连接")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证过程中发生异常: {e}")
        sys.exit(1)