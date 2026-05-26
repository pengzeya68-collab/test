"""
代码沙盒服务测试
覆盖代码执行、超时处理、错误处理
"""
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from fastapi_backend.services.sandbox_service import CodeSandbox


class TestSandbox:
    """沙盒服务测试"""

    def setup_method(self):
        self.sandbox = CodeSandbox()

    @pytest.mark.asyncio
    async def test_execute_python_success(self):
        with patch("fastapi_backend.services.sandbox_service.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = MagicMock()
            mock_proc.communicate = AsyncMock(return_value=(b"hello world\n", b""))
            mock_proc.returncode = 0
            mock_proc.kill = MagicMock()
            mock_subprocess.return_value = mock_proc

            result = await self.sandbox.execute_code("print('hello world')", "python")

            assert result["exit_code"] == 0
            assert "hello world" in result["stdout"]
            assert result["stderr"] == ""

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        with patch("fastapi_backend.services.sandbox_service.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = MagicMock()
            # 用普通函数模拟超时，避免创建未 await 的 AsyncMock
            mock_proc.communicate = MagicMock(side_effect=asyncio.TimeoutError)
            mock_proc.returncode = None
            mock_proc.kill = MagicMock()
            mock_subprocess.return_value = mock_proc

            result = await self.sandbox.execute_code("while True: pass", "python", timeout=1)

            # TimeoutError 被捕获，exit_code 应为 -1
            assert result["exit_code"] == -1

    @pytest.mark.asyncio
    async def test_execute_runtime_error(self):
        with patch("fastapi_backend.services.sandbox_service.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = MagicMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b"NameError: name 'x' is not defined"))
            mock_proc.returncode = 1
            mock_proc.kill = MagicMock()
            mock_subprocess.return_value = mock_proc

            result = await self.sandbox.execute_code("print(x)", "python")

            assert result["exit_code"] == 1
            assert "NameError" in result["stderr"]

    @pytest.mark.asyncio
    async def test_execute_invalid_language(self):
        result = await self.sandbox.execute_code("print('test')", "unsupported_lang")

        assert result["exit_code"] == -1
        assert "不支持" in result["stderr"]

    @pytest.mark.asyncio
    async def test_execute_large_output(self):
        large_output = "x" * 20000
        with patch("fastapi_backend.services.sandbox_service.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = MagicMock()
            mock_proc.communicate = AsyncMock(return_value=(large_output.encode(), b""))
            mock_proc.returncode = 0
            mock_proc.kill = MagicMock()
            mock_subprocess.return_value = mock_proc

            result = await self.sandbox.execute_code("print('x' * 20000)", "python")

            assert result["exit_code"] == 0
            assert len(result["stdout"]) <= 1024 * 10 + 64
            assert "输出被截断" in result["stdout"]

    @pytest.mark.asyncio
    async def test_security_blocked_import(self):
        result = await self.sandbox.execute_code("import os\nos.system('ls')", "python")

        assert result["exit_code"] == -1
        assert "安全检查失败" in result["stderr"]

    @pytest.mark.asyncio
    async def test_security_blocked_builtin(self):
        result = await self.sandbox.execute_code("eval('1+1')", "python")

        assert result["exit_code"] == -1
        assert "安全检查失败" in result["stderr"]

    @pytest.mark.asyncio
    async def test_execute_empty_code(self):
        result = await self.sandbox.execute_code("", "python")

        assert result["exit_code"] == -1
        assert "非空字符串" in result["stderr"]
