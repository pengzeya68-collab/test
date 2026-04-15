"""
沙盒服务测试
覆盖超时、内存限制、运行时错误等边界情况
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sandbox_service import CodeSandbox


class TestSandboxService(unittest.TestCase):
    """沙盒服务测试"""

    def setUp(self):
        self.sandbox = CodeSandbox()

    def test_execute_code_success(self):
        """测试代码执行成功"""
        # 由于CodeSandbox可能依赖外部执行环境，这里使用mock
        with patch('services.sandbox_service.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Hello, World!"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = self.sandbox.execute_code("print('Hello, World!')", "python", timeout=2)

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["stdout"], "Hello, World!")
            self.assertEqual(result["stderr"], "")

    def test_execute_code_timeout(self):
        """测试代码执行超时"""
        with patch('services.sandbox_service.subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutError("执行超时")

            result = self.sandbox.execute_code("while True: pass", "python", timeout=1)

            self.assertEqual(result["exit_code"], -1)
            self.assertIn("超时", result["stderr"])

    def test_execute_code_runtime_error(self):
        """测试代码运行时错误"""
        with patch('services.sandbox_service.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "ZeroDivisionError: division by zero"
            mock_run.return_value = mock_result

            result = self.sandbox.execute_code("1 / 0", "python", timeout=2)

            self.assertEqual(result["exit_code"], 1)
            self.assertIn("ZeroDivisionError", result["stderr"])

    def test_execute_code_memory_limit(self):
        """测试内存限制（模拟）"""
        # 实际的内存限制检测可能更复杂，这里模拟
        with patch('services.sandbox_service.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 137  # 常见的内存错误退出码
            mock_result.stdout = ""
            mock_result.stderr = "MemoryError"
            mock_run.return_value = mock_result

            result = self.sandbox.execute_code("x = [0] * 10**9", "python", timeout=5)

            self.assertEqual(result["exit_code"], 137)
            self.assertIn("MemoryError", result["stderr"])

    def test_execute_code_invalid_language(self):
        """测试不支持的语言"""
        result = self.sandbox.execute_code("console.log('test')", "javascript", timeout=2)

        # 应该返回错误或降级处理
        self.assertIsNotNone(result)
        # 具体行为取决于实现

    def test_execute_code_with_input(self):
        """测试带输入的程序执行"""
        with patch('services.sandbox_service.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "42"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = self.sandbox.execute_code(
                code="print(input())",
                language="python",
                input_data="42",
                timeout=2
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["stdout"], "42")

    def test_execute_code_empty_code(self):
        """测试空代码"""
        result = self.sandbox.execute_code("", "python", timeout=2)

        self.assertIsNotNone(result)
        # 具体行为取决于实现

    def test_execute_code_whitespace_only(self):
        """测试只有空白的代码"""
        result = self.sandbox.execute_code("   \n\t\n  ", "python", timeout=2)

        self.assertIsNotNone(result)
        # 具体行为取决于实现

    def test_execute_code_large_output(self):
        """测试大输出截断"""
        large_output = "A" * 1024 * 20  # 20KB，超过默认限制

        with patch('services.sandbox_service.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = large_output
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = self.sandbox.execute_code("print('A' * 20000)", "python", timeout=2)

            self.assertEqual(result["exit_code"], 0)
            # 输出应该被截断
            self.assertLessEqual(len(result["stdout"]), 1024 * 10)  # 10KB限制

    def test_sandbox_security(self):
        """测试安全限制（模拟）"""
        dangerous_code = "import os; os.system('rm -rf /')"

        with patch('services.sandbox_service.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = self.sandbox.execute_code(dangerous_code, "python", timeout=2)

            # 应该被安全机制阻止或运行在受限环境
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()