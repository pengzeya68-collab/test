#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TestMaster服务验证脚本
用于验证FastAPI服务和主要功能模块
"""
import os
import sys
import json
import time
import requests
import sqlite3
from typing import Dict, List, Optional, Tuple

# 设置Windows控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class ServiceValidator:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.session = requests.Session()
        self.test_results = []
        self.headers = {}

    def log_result(self, module: str, test: str, success: bool, message: str = "", details: Optional[Dict] = None):
        """记录测试结果"""
        status = "✅" if success else "❌"
        self.test_results.append({
            "module": module,
            "test": test,
            "success": success,
            "message": message,
            "details": details
        })
        print(f"  {status} {test:40} {message}")

    def check_service_health(self) -> bool:
        """检查服务健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_result("系统", "服务健康检查", True, "服务正常运行")
                    return True
                else:
                    self.log_result("系统", "服务健康检查", False, f"服务状态异常: {data}")
                    return False
            else:
                self.log_result("系统", "服务健康检查", False, f"HTTP状态码: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_result("系统", "服务健康检查", False, f"连接失败: {str(e)}")
            return False

    def test_database_connection(self) -> bool:
        """测试数据库连接"""
        db_path = r"C:\Users\lenovo\Desktop\TestMasterProject\instance\testmaster.db"
        if not os.path.exists(db_path):
            self.log_result("数据库", "数据库文件检查", False, f"数据库文件不存在: {db_path}")
            return False

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查关键表
            tables_to_check = ["users", "exercises", "exams", "interview_questions", "interface_test_cases"]

            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.log_result("数据库", f"表 {table} 检查", True, f"存在, {count} 行数据")
                except sqlite3.Error as e:
                    self.log_result("数据库", f"表 {table} 检查", False, f"错误: {str(e)}")

            conn.close()
            self.log_result("数据库", "数据库连接", True, "数据库连接正常")
            return True

        except Exception as e:
            self.log_result("数据库", "数据库连接", False, f"连接异常: {str(e)}")
            return False

    def test_auth_endpoints(self):
        """测试认证端点"""
        # 测试管理员登录
        login_data = {
            "username": "admin",
            "password": "admin123"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.headers["Authorization"] = f"Bearer {data['access_token']}"
                    self.session.headers.update(self.headers)
                    self.log_result("用户认证", "管理员登录", True, "登录成功")
                else:
                    self.log_result("用户认证", "管理员登录", False, "响应中没有access_token")
            else:
                self.log_result("用户认证", "管理员登录", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_result("用户认证", "管理员登录", False, f"请求异常: {str(e)}")

    def test_api_endpoints(self):
        """测试API端点"""
        endpoints = [
            ("学习系统", "/api/learning-paths", "GET"),
            ("习题管理", "/api/exercises", "GET"),
            ("考试系统", "/api/exams", "GET"),
            ("面试系统", "/api/interview/questions", "GET"),
            ("自动化测试", "/api/auto-test/cases", "GET"),
            ("技能统计", "/api/skills", "GET"),
            ("诊断功能", "/api/auto-test/diagnose/data-consistency", "GET"),
            ("后台管理", "/api/admin/users", "GET"),
        ]

        for module, endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=10)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", headers=self.headers, timeout=10)
                else:
                    continue

                if response.status_code in [200, 201]:
                    self.log_result(module, f"{method} {endpoint}", True, f"请求成功")
                else:
                    self.log_result(module, f"{method} {endpoint}", False, f"HTTP状态码: {response.status_code}")
            except Exception as e:
                self.log_result(module, f"{method} {endpoint}", False, f"请求异常: {str(e)}")

    def test_automation_testing(self):
        """测试自动化测试功能"""
        try:
            # 测试用例列表
            response = self.session.get(f"{self.base_url}/api/auto-test/cases", headers=self.headers, timeout=10)
            if response.status_code == 200:
                cases = response.json()
                self.log_result("自动化测试", "获取用例列表", True, f"获取到 {len(cases)} 个用例")

            # 测试分组列表
            response = self.session.get(f"{self.base_url}/api/auto-test/groups", headers=self.headers, timeout=10)
            if response.status_code == 200:
                self.log_result("自动化测试", "获取分组列表", True, "请求成功")

            # 测试诊断功能
            response = self.session.get(f"{self.base_url}/api/auto-test/diagnose/data-consistency", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result("自动化测试", "数据一致性诊断", True, "诊断功能正常")
        except Exception as e:
            self.log_result("自动化测试", "功能测试", False, f"测试异常: {str(e)}")

    def check_frontend_connection(self):
        """检查前端连接"""
        try:
            response = self.session.get("http://localhost:5173", timeout=10)
            if response.status_code == 200:
                self.log_result("前端", "前端服务连接", True, "前端服务运行正常")
            else:
                self.log_result("前端", "前端服务连接", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_result("前端", "前端服务连接", False, f"连接失败: {str(e)}")

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("\n" + "="*80)
        print("TestMaster服务功能验证")
        print("="*80)

        # 1. 检查服务健康
        print("\n1. 检查服务状态:")
        service_ok = self.check_service_health()

        if not service_ok:
            print("\n⚠️  服务未运行，请先启动FastAPI服务！")
            print("   使用: .\\start_all.bat 或 .\\TestMaster一键启动.bat")
            return False

        # 2. 检查数据库
        print("\n2. 检查数据库:")
        self.test_database_connection()

        # 3. 测试认证
        print("\n3. 测试用户认证:")
        self.test_auth_endpoints()

        # 4. 测试API端点
        print("\n4. 测试API端点:")
        self.test_api_endpoints()

        # 5. 测试自动化测试
        print("\n5. 测试自动化测试:")
        self.test_automation_testing()

        # 6. 检查前端
        print("\n6. 检查前端服务:")
        self.check_frontend_connection()

        # 7. 生成报告
        print("\n" + "="*80)
        print("验证报告:")
        print("-"*80)

        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)

        print(f"总计: {total} 项测试")
        print(f"通过: {passed} 项")
        print(f"失败: {total - passed} 项")

        # 按模块统计
        modules = {}
        for result in self.test_results:
            module = result["module"]
            if module not in modules:
                modules[module] = {"passed": 0, "total": 0}
            modules[module]["total"] += 1
            if result["success"]:
                modules[module]["passed"] += 1

        print("\n模块详情:")
        for module, stats in modules.items():
            success_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"  {module:15} {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")

        print("\n" + "="*80)
        if passed == total:
            print("🎉 所有测试通过！服务功能完整。")
            return True
        else:
            print("⚠️  部分测试失败，请检查服务状态和配置。")
            return False


def main():
    """主函数"""
    print("TestMaster服务功能验证工具")
    print("本工具将验证FastAPI服务的所有主要功能。")
    print("")
    print("准备工作:")
    print("1. 确保FastAPI服务已启动")
    print("2. 确保前端服务已启动（可选）")
    print("3. 确保数据库文件存在")
    print("")

    validator = ServiceValidator()
    success = validator.run_all_tests()

    if success:
        print("\n✅ 验证成功！所有核心功能正常工作。")
    else:
        print("\n❌ 验证发现一些问题，请检查上述报告。")

    print("\n服务访问地址:")
    print("  后端API: http://localhost:5001/api/docs")
    print("  前端界面: http://localhost:5173")
    print("")

    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)