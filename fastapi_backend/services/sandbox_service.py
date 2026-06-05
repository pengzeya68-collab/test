import asyncio
import logging
import os
import platform
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi_backend.core.config import settings

logger = logging.getLogger(__name__)


class CodeSandbox:
    LANGUAGE_CONFIG = {
        "python": {"command": "python", "extension": ".py", "timeout": 5},
        "sql": {"command": "sqlite3", "extension": ".sql", "timeout": 3},
        "shell": {"command": "bash", "extension": ".sh", "timeout": 5},
    }

    # 语言别名映射：将各种变体统一为标准语言名
    LANGUAGE_ALIASES = {
        "python3": "python",
        "python2": "python",
        "py": "python",
        "bash": "shell",
        "sh": "shell",
        "zsh": "shell",
        "sqlite": "sql",
        "mysql": "sql",
        "postgresql": "sql",
        "pgsql": "sql",
        "中文": "python",  # 中文理论题中的代码题默认按python处理
    }

    # 并发限制：同时运行的沙箱进程数
    _concurrency_semaphore = asyncio.Semaphore(10)

    BLOCKED_BUILTINS = frozenset(
        {
            "exec",
            "eval",
            "compile",
            "__import__",
            "breakpoint",
            "exit",
            "quit",
        }
    )

    BLOCKED_MODULES = frozenset(
        {
            "os",
            "sys",
            "subprocess",
            "shutil",
            "socket",
            "ctypes",
            "pickle",
            "marshal",
            "importlib",
            "signal",
            "resource",
            "multiprocessing",
            "threading",
            "asyncio",
            "webbrowser",
        }
    )

    def _truncate_output(self, text: str, max_length: int = None) -> str:
        if max_length is None:
            max_length = settings.SANDBOX_MAX_OUTPUT_LENGTH
        if len(text) <= max_length:
            return text
        truncated = text[:max_length]
        return f"{truncated}\n... [输出被截断，超过 {max_length} 字符限制]"

    def _validate_timeout(self, timeout: int) -> tuple[bool, str]:
        if timeout < 1:
            return False, f"超时时间必须大于等于1秒，当前: {timeout}"
        if timeout > settings.SANDBOX_MAX_TIMEOUT_SECONDS:
            return (
                False,
                f"超时时间不能超过 {settings.SANDBOX_MAX_TIMEOUT_SECONDS} 秒，当前: {timeout}",
            )
        return True, ""

    def _is_code_safe(self, code: str, language: str) -> tuple[bool, str]:
        # 移除注释和字符串中的内容，防止绕过
        code_stripped = re.sub(r"#[^\n]*", "", code)  # 移除单行注释
        code_stripped = re.sub(r'"""[\s\S]*?"""', "", code_stripped)  # 移除多行字符串
        code_stripped = re.sub(r"'''[\s\S]*?'''", "", code_stripped)  # 移除多行字符串
        code_lower = code_stripped.lower()
        code_original = code_stripped

        DANGEROUS_PATTERNS = [
            r"\brm\s+-[rf]*",
            r"\brmdir\s+",
            r"\bdel\s+",
            r"\bformat\s+",
            r"\bmkfs\.",
            r"\bdd\s+if=",
            r"\bshred\s+",
            r"\bshutdown\b",
            r"\breboot\b",
            r"\bhalt\b",
            r"\bpoweroff\b",
            r"\bsudo\b",
            r"\bsu\s+-",
            r"\bdoas\b",
            r"\bwget\s+",
            r"\bcurl\s+.*-[oO]",
            r"\bscp\s+",
            r"\bsftp\b",
            r"\bftp\b",
            r"\bnc\s+",
            r"\bnetcat\b",
            r"\bpip\s+(install|uninstall)",
            r"\bconda\s+install",
            r"\bapt\s+(install|remove|purge)",
            r"\byum\s+install",
            r"\bdnf\s+install",
            r"\bbrew\s+install",
            r"\bapk\s+add",
            r"\bnpm\s+(install|i)\s",
            r"\byarn\s+add",
            r"\bchmod\s+",
            r"\bchown\s+",
            r"\bchgrp\s+",
            r"\bos\.system\s*\(",
            r"\bos\.popen\s*\(",
            r"\bsubprocess\.",
            r"\b__import__\s*\(",
            r"\bimportlib\.",
            r"\bgetattr\s*\(",
            r"\b__builtins__\b",
            r"\bos\.remove\b",
            r"\bos\.unlink\b",
            r"\bshutil\.",
            r"\bsocket\.",
            r"\bctypes\.",
            r"\bpickle\.",
            r"\bmarshal\.",
            r"[|;&]\s*\b(?:rm|del|format|shutdown)\b",
            r"`[^`]*\b(?:rm|del|format)\b[^`]*`",
            r"\$\([^)]*\b(?:rm|del|format)\b[^)]*\)",
            r"\.\./",
            r"\.\.\\",
            r"~/\.",
            r"/etc/passwd",
            r"/etc/shadow",
            r"\bnmap\b",
            r"\bping\s+-[cf]",
            r"\btraceroute\b",
        ]

        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, code_lower):
                return False, "检测到危险代码模式"

        if language == "python":
            # 增强的模块检测：包括别名导入、间接导入等
            for mod in self.BLOCKED_MODULES:
                patterns = [
                    rf"\bimport\s+{mod}\b",
                    rf"\bfrom\s+{mod}\b",
                    rf"\bimport\s+{mod}\s+as\s+\w+",
                    rf"\bfrom\s+{mod}\s+import\s+",
                    # 检测字符串形式的模块引用
                    rf"['\"]{mod}['\"]",
                ]
                for pattern in patterns:
                    if re.search(pattern, code_lower):
                        return False, f"禁止导入模块: {mod}"

            # 检测危险内置函数
            for builtin_name in self.BLOCKED_BUILTINS:
                # 改进：支持各种调用方式，包括带空格、括号内换行等
                if re.search(rf"\b{builtin_name}\s*\(", code_original):
                    return False, f"禁止使用内置函数: {builtin_name}"

            # 检测文件操作
            if re.search(r"\bopen\s*\(", code_original):
                return False, "禁止使用 open() 函数"

            # 检测 exec/eval 的各种变体
            if re.search(r"\bexec\s*\(", code_original) or re.search(r"\beval\s*\(", code_original):
                return False, "禁止使用 exec/eval"

            # 检测 compile
            if re.search(r"\bcompile\s*\(", code_original):
                return False, "禁止使用 compile()"

            # 额外安全检查：检测 type.mro() 链、__subclasses__() 等高级绕过技术
            advanced_bypass_patterns = [
                r"\btype\s*\([^)]*\)\s*\.\s*mro\s*\(",
                r"\b__subclasses__\s*\(",
                r"\b__bases__\b",
                r"\b__globals__\b",
                r"\b__code__\b",
                r"\b__class__\b",
                r"\b__mro__\b",
                r"\b__dict__\b",
                r"\bvars\s*\(",
                r"\bdir\s*\(",
                r"\bglobals\s*\(",
                r"\blocals\s*\(",
                r"\bgetattr\s*\(",
                r"\bsetattr\s*\(",
                r"\bdelattr\s*\(",
                r"\bhasattr\s*\(",
            ]
            for pattern in advanced_bypass_patterns:
                if re.search(pattern, code_original):
                    return False, "检测到潜在的沙箱绕过技术"

        if language == "shell":
            lines = code.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("#"):
                    continue
                if re.search(r"\b(?:bash|sh|zsh)\s+-c\s+", line):
                    return False, "禁止嵌套执行shell命令"
                # 检测 base64 编码执行
                if re.search(r"\bbase64\s+(-d|--decode)\b", line):
                    return False, "禁止 base64 解码执行"
                # 检测 eval 变量替换
                if re.search(r"\beval\s+", line):
                    return False, "禁止使用 eval"

        return True, "安全"

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        input_data: str = None,
        timeout: int = None,
        setup_sql: str = None,
    ) -> dict:
        # 标准化语言名称：小写 + 别名映射
        language = language.lower().strip()
        language = self.LANGUAGE_ALIASES.get(language, language)

        if language not in self.LANGUAGE_CONFIG:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"不支持的语言：{language}",
                "execution_time_ms": 0,
            }

        safe, msg = self._is_code_safe(code, language)
        if not safe:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"安全检查失败：{msg}",
                "execution_time_ms": 0,
            }

        if timeout is None:
            timeout = self.LANGUAGE_CONFIG[language]["timeout"]

        if language == "python":
            return await self._execute_python(code, input_data, timeout)
        elif language == "sql":
            return await self._execute_sql(code, timeout, setup_sql=setup_sql)
        elif language == "shell":
            return await self._execute_shell(code, timeout)
        else:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"未实现的语言：{language}",
                "execution_time_ms": 0,
            }

    async def _execute_python(self, code: str, input_data: str = None, timeout: int = None) -> dict:
        if timeout is None:
            timeout = settings.SANDBOX_DEFAULT_TIMEOUT_SECONDS

        timeout_valid, timeout_msg = self._validate_timeout(timeout)
        if not timeout_valid:
            logger.warning(f"超时时间验证失败: {timeout_msg}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": timeout_msg,
                "execution_time_ms": 0,
            }

        if not isinstance(code, str) or not code.strip():
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "代码输入必须是非空字符串",
                "execution_time_ms": 0,
            }

        logger.info(f"开始执行 Python 代码, timeout={timeout}s, has_input={input_data is not None}")

        # 使用信号量限制并发
        async with self._concurrency_semaphore:
            start_time = time.perf_counter()
            temp_path: Optional[Path] = None
            process = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".py",
                    prefix="sandbox_",
                    delete=False,
                    encoding="utf-8",
                ) as temp_file:
                    temp_file.write(code)
                    temp_path = Path(temp_file.name)

                safe_env = {
                    "PATH": os.environ.get("PATH", ""),
                    "PYTHONPATH": "",
                    "HOME": os.environ.get("HOME", ""),
                    "USER": os.environ.get("USER", ""),
                    "TMPDIR": tempfile.gettempdir(),
                }

                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-I",
                    str(temp_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if input_data else asyncio.subprocess.DEVNULL,
                    cwd=tempfile.gettempdir(),
                    env=safe_env,
                )

                try:
                    if input_data:
                        stdout_bytes, stderr_bytes = await asyncio.wait_for(
                            process.communicate(input=input_data.encode("utf-8")),
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

                stdout = self._truncate_output(stdout_bytes.decode("utf-8", errors="replace"))
                stderr = self._truncate_output(stderr_bytes.decode("utf-8", errors="replace"))
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
                    except OSError as e:
                        logger.warning(f"清理临时文件失败: {e}")

    async def execute_python_code(self, code: str, timeout: int = None) -> dict:
        return await self._execute_python(code, input_data=None, timeout=timeout)

    async def execute_python_code_with_input(self, code: str, input_data: str = None, timeout: int = None) -> dict:
        return await self._execute_python(code, input_data=input_data, timeout=timeout)

    async def _execute_sql(self, code: str, timeout: int = None, setup_sql: str = None) -> dict:
        import sqlite3
        import re

        if timeout is None:
            timeout = self.LANGUAGE_CONFIG["sql"]["timeout"]

        # 白名单策略：只允许安全的只读语句
        def is_safe_sql(stmt: str) -> tuple[bool, str]:
            stmt_upper = stmt.strip().upper()
            # 允许的语句类型
            allowed_prefixes = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "PRAGMA")
            if not any(stmt_upper.startswith(prefix) for prefix in allowed_prefixes):
                return False, "只允许 SELECT/SHOW/DESCRIBE/EXPLAIN/PRAGMA 语句"
            # 检测危险关键字
            dangerous_keywords = [
                r"\bINSERT\b",
                r"\bUPDATE\b",
                r"\bDELETE\b",
                r"\bDROP\b",
                r"\bCREATE\b",
                r"\bALTER\b",
                r"\bTRUNCATE\b",
                r"\bREPLACE\b",
                r"\bGRANT\b",
                r"\bREVOKE\b",
                r"\bEXEC\b",
                r"\bEXECUTE\b",
                r"\bVACUUM\b",
                r"\bATTACH\b",
                r"\bDETACH\b",
                r"\bLOAD_EXTENSION\b",
            ]
            for pattern in dangerous_keywords:
                if re.search(pattern, stmt_upper):
                    return False, f"检测到危险关键字: {pattern}"
            return True, ""

        # setup_sql 安全检查：允许 DDL 但禁止危险操作
        def is_safe_setup_sql(stmt: str) -> tuple[bool, str]:
            stmt_upper = stmt.strip().upper()
            # setup_sql 中禁止的危险关键字（允许 CREATE/INSERT/UPDATE/DELETE 用于建表和初始化数据）
            dangerous_keywords = [
                r"\bATTACH\b",
                r"\bDETACH\b",
                r"\bLOAD_EXTENSION\b",
                r"\bGRANT\b",
                r"\bREVOKE\b",
                r"\bVACUUM\b",
            ]
            for pattern in dangerous_keywords:
                if re.search(pattern, stmt_upper):
                    return False, f"setup_sql 中检测到危险关键字: {pattern}"
            return True, ""

        def _sync_execute():
            """同步执行 SQL，用于在线程池中运行"""
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            output = []
            # 设置超时：使用 set_progress_handler 每 100ms 检查是否超时
            import time as _time
            _start_time = _time.monotonic()
            _timeout_ms = int(timeout * 1000) if timeout else 5000

            def _progress_check():
                if (_time.monotonic() - _start_time) * 1000 > _timeout_ms:
                    raise sqlite3.OperationalError("SQL 执行超时")

            conn.set_progress_handler(_progress_check, 100)

            try:
                cursor = conn.cursor()

                # setup_sql 用于建表和初始数据，允许执行 DDL 但需安全检查
                if setup_sql and setup_sql.strip():
                    for stmt in setup_sql.split(";"):
                        stmt = stmt.strip()
                        if stmt:
                            safe, msg = is_safe_setup_sql(stmt)
                            if not safe:
                                return {
                                    "exit_code": 1,
                                    "stdout": "",
                                    "stderr": f"setup_sql 安全检查失败：{msg}",
                                    "execution_time_ms": 0,
                                }
                            try:
                                cursor.execute(stmt)
                            except sqlite3.Error:
                                pass
                    conn.commit()

                statements = [s.strip() for s in code.split(";") if s.strip()]

                for statement in statements:
                    # 安全检查：只允许只读查询
                    safe, msg = is_safe_sql(statement)
                    if not safe:
                        return {
                            "exit_code": 1,
                            "stdout": "\n".join(output),
                            "stderr": f"安全检查失败：{msg}",
                            "execution_time_ms": 0,
                        }

                    try:
                        cursor.execute(statement)
                        rows = cursor.fetchall()
                        if rows:
                            columns = [description[0] for description in cursor.description]
                            output.append("\t".join(columns))
                            output.append("-" * 40)
                            for row in rows:
                                output.append("\t".join(str(cell) for cell in row))
                        else:
                            output.append("(没有数据)")
                    except sqlite3.Error as e:
                        output.append(f"SQL错误: {str(e)}")
                        return {
                            "exit_code": 1,
                            "stdout": "\n".join(output),
                            "stderr": str(e),
                            "execution_time_ms": 0,
                        }

                return {
                    "exit_code": 0,
                    "stdout": "\n".join(output) if output else "执行成功",
                    "stderr": "",
                    "execution_time_ms": 0,
                }
            except Exception as e:
                return {
                    "exit_code": 1,
                    "stdout": "\n".join(output) if output else "",
                    "stderr": str(e),
                    "execution_time_ms": 0,
                }
            finally:
                conn.close()

        # 使用 asyncio.to_thread() 将同步操作包装在独立线程中，避免阻塞事件循环
        return await asyncio.to_thread(_sync_execute)

    async def _execute_shell(self, code: str, timeout: int = None) -> dict:
        if timeout is None:
            timeout = self.LANGUAGE_CONFIG["shell"]["timeout"]

        # 使用信号量限制并发
        async with self._concurrency_semaphore:
            is_windows = platform.system() == "Windows"
            if is_windows:
                shell_cmd = "powershell.exe"
                suffix = ".ps1"
            else:
                shell_cmd = "bash"
                suffix = ".sh"

            with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
                f.write(code)
                temp_file = f.name

            try:
                # 设置安全的环境变量
                safe_env = {
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", ""),
                    "USER": os.environ.get("USER", ""),
                    "TMPDIR": tempfile.gettempdir(),
                }

                if is_windows:
                    process = await asyncio.create_subprocess_exec(
                        shell_cmd,
                        "-ExecutionPolicy", "Bypass",
                        "-File", temp_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        stdin=asyncio.subprocess.DEVNULL,
                        cwd=tempfile.gettempdir(),
                        env=safe_env,
                    )
                else:
                    process = await asyncio.create_subprocess_exec(
                        shell_cmd,
                        temp_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        stdin=asyncio.subprocess.DEVNULL,
                        cwd=tempfile.gettempdir(),
                        env=safe_env,
                    )
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.communicate()
                    return {
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": f"Shell执行超时（超过{timeout}秒）",
                        "execution_time_ms": 0,
                    }

                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")

                return {
                    "exit_code": process.returncode if process.returncode is not None else -1,
                    "stdout": stdout,
                    "stderr": stderr,
                    "execution_time_ms": 0,
                }
            finally:
                os.unlink(temp_file)
