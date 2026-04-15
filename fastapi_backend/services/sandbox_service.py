import asyncio
import logging
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi_backend.core.config import settings

logger = logging.getLogger(__name__)


class CodeSandbox:
    # 支持的语言配置
    LANGUAGE_CONFIG = {
        'python': {
            'command': 'python',
            'extension': '.py',
            'timeout': 5  # 执行超时时间，秒
        },
        'sql': {
            'command': 'sqlite3',
            'extension': '.sql',
            'timeout': 3
        },
        'shell': {
            'command': 'bash',
            'extension': '.sh',
            'timeout': 5
        }
    }

    def _truncate_output(self, text: str, max_length: int = None) -> str:
        """截断输出文本，避免过大输出占用内存"""
        if max_length is None:
            max_length = settings.SANDBOX_MAX_OUTPUT_LENGTH

        if len(text) <= max_length:
            return text

        truncated = text[:max_length]
        # 添加截断提示
        return f"{truncated}\n... [输出被截断，超过 {max_length} 字符限制]"

    def _validate_timeout(self, timeout: int) -> tuple[bool, str]:
        """验证超时时间是否在允许范围内"""
        if timeout < 1:
            return False, f"超时时间必须大于等于1秒，当前: {timeout}"
        if timeout > settings.SANDBOX_MAX_TIMEOUT_SECONDS:
            return False, f"超时时间不能超过 {settings.SANDBOX_MAX_TIMEOUT_SECONDS} 秒，当前: {timeout}"
        return True, ""

    def _is_code_safe(self, code: str, language: str) -> tuple[bool, str]:
        """检查代码是否安全 - 使用正则表达式进行精确匹配"""
        code_lower = code.lower()

        # 危险模式列表（从Flask后端复制）
        DANGEROUS_PATTERNS = [
            # 文件删除命令
            r'\brm\s+-[rf]*', r'\brmdir\s+', r'\bdel\s+', r'\bformat\s+',
            r'\bmkfs\.', r'\bdd\s+if=', r'\bshred\s+',
            # 系统控制命令
            r'\bshutdown\b', r'\breboot\b', r'\bhalt\b', r'\bpoweroff\b',
            # 权限提升
            r'\bsudo\b', r'\bsu\s+-', r'\bdoas\b',
            # 网络下载
            r'\bwget\s+', r'\bcurl\s+.*-[oO]', r'\bscp\s+', r'\bsftp\b',
            r'\bftp\b', r'\bnc\s+', r'\bnetcat\b',
            # 包管理器
            r'\bpip\s+(install|uninstall)', r'\bconda\s+install',
            r'\bapt\s+(install|remove|purge)', r'\byum\s+install',
            r'\bdnf\s+install', r'\bbrew\s+install', r'\bapk\s+add',
            r'\bnpm\s+(install|i)\s', r'\byarn\s+add',
            # 文件权限修改
            r'\bchmod\s+', r'\bchown\s+', r'\bchgrp\s+',
            # Python危险操作
            r'\bos\.system\s*\(', r'\bos\.popen\s*\(', r'\bsubprocess\.',
            r'\bexec\s*\(', r'\beval\s*\(', r'\bcompile\s*\(',
            r'\b__import__\s*\(', r'\bimportlib\.', r'\bimport\s+os\b',
            r'\bimport\s+sys\b', r'\bimport\s+shutil\b',
            r'\bimport\s+socket\b', r'\bimport\s+ctypes\b',
            r'\bimport\s+pickle\b', r'\bimport\s+marshal\b',
            r'\bfrom\s+os\b', r'\bfrom\s+sys\b', r'\bfrom\s+shutil\b',
            r'\bfrom\s+socket\b', r'\bfrom\s+ctypes\b',
            r'\bfrom\s+pickle\b', r'\bfrom\s+marshal\b',
            r'\bgetattr\s*\(', r'\b__builtins__\b',
            r'\bopen\s*\(', r'\bos\.remove\b', r'\bos\.unlink\b',
            r'\bshutil\.', r'\bsocket\.', r'\bctypes\.',
            r'\bpickle\.', r'\bmarshal\.',
            # Shell危险操作
            r'[|;&]\s*\b(?:rm|del|format|shutdown)\b',
            r'`[^`]*\b(?:rm|del|format)\b[^`]*`',
            r'\$\([^)]*\b(?:rm|del|format)\b[^)]*\)',
            # 路径遍历
            r'\.\./', r'\.\.\\', r'~/\.', r'/etc/passwd', r'/etc/shadow',
            # 网络扫描
            r'\bnmap\b', r'\bping\s+-[cf]', r'\btraceroute\b',
        ]

        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, code_lower):
                return False, f"检测到危险代码模式"

        # 额外的安全检查：禁止多行命令链
        dangerous_chain_chars = [';', '&&', '||', '|']
        if language == 'shell':
            # Shell脚本允许管道，但要检查危险命令
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    continue
                # 检查是否尝试执行危险操作
                if re.search(r'\b(?:bash|sh|zsh)\s+-c\s+', line):
                    return False, "禁止嵌套执行shell命令"

        return True, "安全"

    async def execute_code(self, code: str, language: str = "python", input_data: str = None, timeout: int = None) -> dict:
        """
        安全执行代码，支持多种语言
        """
        # 验证语言支持
        if language not in self.LANGUAGE_CONFIG:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"不支持的语言：{language}",
                "execution_time_ms": 0,
            }

        # 安全检查
        safe, msg = self._is_code_safe(code, language)
        if not safe:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"安全检查失败：{msg}",
                "execution_time_ms": 0,
            }

        # 使用配置的超时时间
        if timeout is None:
            timeout = self.LANGUAGE_CONFIG[language]['timeout']

        # 根据语言执行
        if language == 'python':
            return await self._execute_python(code, input_data, timeout)
        elif language == 'sql':
            return await self._execute_sql(code, timeout)
        elif language == 'shell':
            return await self._execute_shell(code, timeout)
        else:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"未实现的语言：{language}",
                "execution_time_ms": 0,
            }

    async def _execute_python(self, code: str, input_data: str = None, timeout: int = None) -> dict:
        """执行Python代码"""
        if input_data is not None:
            return await self.execute_python_code_with_input(code, input_data, timeout)
        else:
            return await self.execute_python_code(code, timeout)

    async def _execute_sql(self, code: str, timeout: int = None) -> dict:
        """执行SQL代码（使用内存SQLite数据库）"""
        import sqlite3
        import asyncio

        # 创建内存数据库
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row

        # 捕获输出
        output = []

        try:
            cursor = conn.cursor()

            # 分割多条SQL语句
            statements = [s.strip() for s in code.split(';') if s.strip()]

            for statement in statements:
                try:
                    cursor.execute(statement)

                    # 如果是SELECT语句，获取结果
                    if statement.upper().startswith('SELECT'):
                        rows = cursor.fetchall()
                        if rows:
                            # 获取列名
                            columns = [description[0] for description in cursor.description]
                            output.append('\t'.join(columns))
                            output.append('-' * 40)
                            for row in rows:
                                output.append('\t'.join(str(cell) for cell in row))
                        else:
                            output.append("(没有数据)")
                    else:
                        conn.commit()
                        output.append(f"执行成功，影响行数: {cursor.rowcount}")

                except sqlite3.Error as e:
                    output.append(f"SQL错误: {str(e)}")
                    return {
                        "exit_code": 1,
                        "stdout": '\n'.join(output),
                        "stderr": str(e),
                        "execution_time_ms": 0,
                    }

            return {
                "exit_code": 0,
                "stdout": '\n'.join(output) if output else "执行成功",
                "stderr": '',
                "execution_time_ms": 0,
            }

        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": '\n'.join(output) if output else "",
                "stderr": str(e),
                "execution_time_ms": 0,
            }
        finally:
            conn.close()

    async def _execute_shell(self, code: str, timeout: int = None) -> dict:
        """执行Shell代码"""
        import asyncio
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name

        try:
            process = await asyncio.create_subprocess_exec(
                'bash', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=tempfile.gettempdir(),
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutExpired:
                process.kill()
                await process.communicate()
                return {
                    "exit_code": -1,
                    "stdout": '',
                    "stderr": f'Shell执行超时（超过{timeout}秒）',
                    "execution_time_ms": 0,
                }

            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')

            return {
                "exit_code": process.returncode if process.returncode is not None else -1,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time_ms": 0,  # 暂时不计算执行时间
            }
        finally:
            os.unlink(temp_file)

    async def execute_python_code(self, code: str, timeout: int = None) -> dict:
        """
        安全执行 Python 代码

        Args:
            code: Python 源代码
            timeout: 执行超时时间（秒）

        Returns:
            包含执行结果的字典
        """
        # 使用配置的默认超时时间
        if timeout is None:
            timeout = settings.SANDBOX_DEFAULT_TIMEOUT_SECONDS

        logger.info(f"开始执行 Python 代码, timeout={timeout}s")

        # 验证超时时间
        timeout_valid, timeout_msg = self._validate_timeout(timeout)
        if not timeout_valid:
            logger.warning(f"超时时间验证失败: {timeout_msg}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": timeout_msg,
                "execution_time_ms": 0,
            }

        start_time = time.perf_counter()
        temp_path: Optional[Path] = None
        process = None

        try:
            # 1. 验证代码输入
            if not isinstance(code, str) or not code.strip():
                error_msg = "代码输入必须是非空字符串"
                logger.warning(error_msg)
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": error_msg,
                    "execution_time_ms": 0,
                }

            # 2. 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="sandbox_",
                delete=False,
                encoding="utf-8",
            ) as temp_file:
                temp_file.write(code)
                temp_path = Path(temp_file.name)

            # 3. 创建子进程
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-I",
                str(temp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=tempfile.gettempdir(),
                env=None,  # 继承环境变量
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(f"代码执行超时 (timeout={timeout}s)")
                process.kill()
                await process.communicate()
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"代码执行超时，超过 {timeout} 秒限制",
                    "execution_time_ms": int((time.perf_counter() - start_time) * 1000),
                }


            # 4. 获取输出并截断
            stdout_raw = stdout_bytes.decode("utf-8", errors="replace")
            stderr_raw = stderr_bytes.decode("utf-8", errors="replace")

            stdout = self._truncate_output(stdout_raw)
            stderr = self._truncate_output(stderr_raw)

            execution_time_ms = int((time.perf_counter() - start_time) * 1000)

            logger.info(f"执行完成, exit_code={process.returncode}, execution_time={execution_time_ms}ms")

            return {
                "exit_code": process.returncode if process.returncode is not None else -1,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time_ms": execution_time_ms,
            }
        except FileNotFoundError:
            error_msg = "未找到 Python 运行时，无法执行代码"
            logger.error(error_msg)
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": error_msg,
                "execution_time_ms": int((time.perf_counter() - start_time) * 1000),
            }
        except Exception as exc:
            error_msg = f"沙盒执行失败: {exc}"
            logger.error(error_msg)
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": error_msg,
                "execution_time_ms": int((time.perf_counter() - start_time) * 1000),
            }
        finally:
            if process and process.returncode is None:
                logger.warning("进程仍在运行，强制终止")
                process.kill()
                try:
                    await process.communicate()
                except Exception as e:
                    logger.warning(f"终止进程时出错: {e}")

            if temp_path and temp_path.exists():
                try:
                    os.remove(temp_path)
                    logger.info(f"清理临时文件: {temp_path}")
                except OSError as e:
                    logger.warning(f"清理临时文件失败: {e}")

    async def execute_python_code_with_input(self, code: str, input_data: str = None, timeout: int = None) -> dict:
        """
        安全执行 Python 代码并传递输入到标准输入

        Args:
            code: Python 源代码
            input_data: 输入字符串，将传递给程序的标准输入
            timeout: 执行超时时间（秒）

        Returns:
            包含执行结果的字典
        """
        # 使用配置的默认超时时间
        if timeout is None:
            timeout = settings.SANDBOX_DEFAULT_TIMEOUT_SECONDS

        logger.info(f"开始执行 Python 代码（带输入）, timeout={timeout}s, input_length={len(input_data) if input_data else 0}")

        # 验证超时时间
        timeout_valid, timeout_msg = self._validate_timeout(timeout)
        if not timeout_valid:
            logger.warning(f"超时时间验证失败: {timeout_msg}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": timeout_msg,
                "execution_time_ms": 0,
            }

        start_time = time.perf_counter()
        temp_path: Optional[Path] = None
        process = None

        try:
            # 1. 验证代码输入
            if not isinstance(code, str) or not code.strip():
                error_msg = "代码输入必须是非空字符串"
                logger.warning(error_msg)
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": error_msg,
                    "execution_time_ms": 0,
                }

            # 2. 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="sandbox_",
                delete=False,
                encoding="utf-8",
            ) as temp_file:
                temp_file.write(code)
                temp_path = Path(temp_file.name)

            # 3. 创建子进程
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-I",
                str(temp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else asyncio.subprocess.DEVNULL,
                cwd=tempfile.gettempdir(),
                env=None,  # 继承环境变量
            )

            try:
                if input_data:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(input=input_data.encode('utf-8')),
                        timeout=timeout,
                    )
                else:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout,
                    )
            except asyncio.TimeoutError:
                logger.warning(f"代码执行超时 (timeout={timeout}s)")
                process.kill()
                await process.communicate()
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"代码执行超时，超过 {timeout} 秒限制",
                    "execution_time_ms": int((time.perf_counter() - start_time) * 1000),
                }


            # 4. 获取输出并截断
            stdout_raw = stdout_bytes.decode("utf-8", errors="replace")
            stderr_raw = stderr_bytes.decode("utf-8", errors="replace")

            stdout = self._truncate_output(stdout_raw)
            stderr = self._truncate_output(stderr_raw)

            execution_time_ms = int((time.perf_counter() - start_time) * 1000)

            logger.info(f"执行完成, exit_code={process.returncode}, execution_time={execution_time_ms}ms")

            return {
                "exit_code": process.returncode if process.returncode is not None else -1,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time_ms": execution_time_ms,
            }
        except FileNotFoundError:
            error_msg = "未找到 Python 运行时，无法执行代码"
            logger.error(error_msg)
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": error_msg,
                "execution_time_ms": int((time.perf_counter() - start_time) * 1000),
            }
        except Exception as exc:
            error_msg = f"沙盒执行失败: {exc}"
            logger.error(error_msg)
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": error_msg,
                "execution_time_ms": int((time.perf_counter() - start_time) * 1000),
            }
        finally:
            if process and process.returncode is None:
                logger.warning("进程仍在运行，强制终止")
                process.kill()
                try:
                    await process.communicate()
                except Exception as e:
                    logger.warning(f"终止进程时出错: {e}")

            if temp_path and temp_path.exists():
                try:
                    os.remove(temp_path)
                    logger.info(f"清理临时文件: {temp_path}")
                except OSError as e:
                    logger.warning(f"清理临时文件失败: {e}")