"""
脚本引擎

提供前置/后置脚本执行能力：
- JavaScript：基于 dukpy（Duktape），提供 pm.* API 兼容层
- Python：基于 RestrictedPython 沙箱，提供 Pythonic 的 pm.* API（对标 Apifox）

复用现有变量系统（context_vars, session_vars, global_vars）。
"""

import json
import logging
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_logger = logging.getLogger(__name__)


class ScriptEngine:
    """JavaScript 脚本执行引擎"""

    @staticmethod
    def build_context(
        context_vars: Dict[str, Any],
        session_vars: Dict[str, Any],
        user_id: Optional[int] = None,
        response_body: Any = None,
        status_code: int = 0,
        response_headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """构建脚本上下文"""
        return {
            "env_vars": dict(context_vars),
            "session_vars": dict(session_vars),
            "user_id": user_id,
            "response_body": response_body,
            "status_code": status_code,
            "response_headers": response_headers or {},
            "test_results": [],
            "globals_to_save": {},
        }

    @staticmethod
    def run_pre_script(code: str, context: Dict[str, Any], language: str = "javascript") -> Dict[str, Any]:
        """执行前置脚本，依据 language 选择 JS 或 Python 引擎"""
        if (language or "javascript").lower() == "python":
            return PythonScriptEngine.run_as_context(code, context, phase="pre")
        return ScriptEngine._execute_script(code, context, phase="pre")

    @staticmethod
    def run_post_script(code: str, context: Dict[str, Any], language: str = "javascript") -> Dict[str, Any]:
        """执行后置脚本，依据 language 选择 JS 或 Python 引擎"""
        if (language or "javascript").lower() == "python":
            return PythonScriptEngine.run_as_context(code, context, phase="post")
        return ScriptEngine._execute_script(code, context, phase="post")

    @staticmethod
    async def persist_globals_to_db(context: Dict[str, Any], source: str = "脚本执行") -> None:
        """
        将脚本中 pm.globals.set 设置的变量持久化到数据库。
        应在脚本执行完成后（且处于异步上下文）调用。
        """
        globals_to_save = context.get("globals_to_save") or {}
        if not globals_to_save:
            return
        try:
            from fastapi_backend.services.autotest_variable_service import save_variables_to_db

            await save_variables_to_db(
                globals_to_save, source=source, user_id=context.get("user_id")
            )
        except Exception as e:
            _logger.warning(f"持久化脚本全局变量失败: {e}")

    @staticmethod
    def _execute_script(code: str, context: Dict[str, Any], phase: str = "pre") -> Dict[str, Any]:
        """
        执行 JS 脚本。尝试使用 dukpy，失败时回退到 Python 模拟执行。
        """
        try:
            return ScriptEngine._execute_with_dukpy(code, context, phase)
        except ImportError:
            _logger.warning("dukpy 未安装，使用 Python 模拟执行脚本")
            return ScriptEngine._execute_with_python(code, context, phase)
        except Exception as e:
            _logger.error(f"脚本执行失败 ({phase}): {e}")
            # 回退到 Python 模拟
            try:
                return ScriptEngine._execute_with_python(code, context, phase)
            except Exception as e2:
                _logger.error(f"Python 模拟执行也失败: {e2}")
                return context

    @staticmethod
    def _execute_with_dukpy(code: str, context: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """使用 dukpy (Duktape JS 引擎) 执行脚本"""
        import dukpy

        env_vars = context.get("env_vars", {})
        session_vars = context.get("session_vars", {})
        variables = context.get("variables", {})

        # 构建 pm 对象的 JS 代码
        pm_bridge = f"""
var pm = {{
    variables: {{
        _data: {json.dumps(variables, ensure_ascii=False)},
        get: function(key) {{ return this._data[key] !== undefined ? this._data[key] : null; }},
        set: function(key, val) {{ this._data[key] = val; }},
        unset: function(key) {{ delete this._data[key]; }},
        toObject: function() {{ return this._data; }}
    }},
    environment: {{
        _data: {json.dumps(env_vars, ensure_ascii=False)},
        get: function(key) {{ return this._data[key] !== undefined ? this._data[key] : null; }},
        set: function(key, val) {{ this._data[key] = val; }},
        unset: function(key) {{ delete this._data[key]; }},
        toObject: function() {{ return this._data; }}
    }},
    sessionVariables: {{
        _data: {json.dumps(session_vars, ensure_ascii=False)},
        get: function(key) {{ return this._data[key] !== undefined ? this._data[key] : null; }},
        set: function(key, val) {{ this._data[key] = val; }},
        unset: function(key) {{ delete this._data[key]; }}
    }},
    globals: {{
        _data: {{}},
        get: function(key) {{ return this._data[key] !== undefined ? this._data[key] : null; }},
        set: function(key, val) {{ this._data[key] = val; __globals_to_save[key] = val; }}
    }},
    response: {{
        _body: {json.dumps(context.get("response_body"), ensure_ascii=False) if context.get("response_body") is not None else "null"},
        _status: {context.get("status_code", 0)},
        _headers: {json.dumps(context.get("response_headers", {}), ensure_ascii=False)},
        json: function() {{
            if (typeof this._body === 'string') {{
                try {{ return JSON.parse(this._body); }} catch(e) {{ return null; }}
            }}
            return this._body;
        }},
        get status() {{ return this._status; }},
        get statusCode() {{ return this._status; }},
        text: function() {{ return typeof this._body === 'string' ? this._body : JSON.stringify(this._body); }},
        headers: {{
            _h: {json.dumps(context.get("response_headers", {}), ensure_ascii=False)},
            get: function(name) {{
                var lower = name.toLowerCase();
                for (var k in this._h) {{
                    if (k.toLowerCase() === lower) return this._h[k];
                }}
                return null;
            }}
        }}
    }},
    test: function(name, fn) {{
        try {{
            fn();
            __test_results.push({{name: name, passed: true}});
        }} catch(e) {{
            __test_results.push({{name: name, passed: false, error: e.message || String(e)}});
        }}
    }},
    expect: function(val) {{
        return {{
            to: {{
                equal: function(expected) {{
                    if (val != expected) throw new Error('Expected ' + JSON.stringify(expected) + ' but got ' + JSON.stringify(val));
                }},
                eql: function(expected) {{
                    if (JSON.stringify(val) !== JSON.stringify(expected)) throw new Error('Deep equal failed');
                }},
                be: {{
                    above: function(n) {{ if (!(val > n)) throw new Error('Expected above ' + n); }},
                    below: function(n) {{ if (!(val < n)) throw new Error('Expected below ' + n); }},
                    a: function(type) {{ if (typeof val !== type) throw new Error('Expected type ' + type); }}
                }},
                include: function(s) {{
                    if (String(val).indexOf(String(s)) === -1) throw new Error('Not contains: ' + s);
                }},
                have: {{
                    property: function(prop) {{
                        if (val === null || val === undefined || !(prop in val)) throw new Error('No property: ' + prop);
                        return {{ that: {{ equals: function(v) {{ if (val[prop] != v) throw new Error('Property mismatch'); }} }} }};
                    }}
                }},
                not: {{
                    equal: function(expected) {{ if (val == expected) throw new Error('Expected not equal'); }}
                }}
            }}
        }};
    }}
}};
var __test_results = [];
var __globals_to_save = {{}};
"""
        # 拼接完整代码：pm 桥接 + 用户脚本 + 返回结果
        result_code = "JSON.stringify({env: pm.environment._data, session: pm.sessionVariables._data, variables: pm.variables._data, tests: __test_results, globals: __globals_to_save})"
        full_code = pm_bridge + "\n" + code + ";\n" + result_code

        # 单次执行，通过返回值获取结果
        result_str = dukpy.evaljs(full_code)

        try:
            result_data = json.loads(result_str) if isinstance(result_str, str) else {}
        except (json.JSONDecodeError, TypeError):
            result_data = {}

        context["env_vars"] = result_data.get("env", env_vars)
        context["session_vars"] = result_data.get("session", session_vars)
        context["variables"] = result_data.get("variables", variables)
        context["test_results"] = result_data.get("tests", [])
        context["globals_to_save"] = result_data.get("globals", {})

        return context

    @staticmethod
    def _execute_with_python(code: str, context: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """
        Python 模拟执行：解析常见的 pm.* API 调用。
        当 dukpy 不可用时的回退方案。
        """

        env_vars = context.get("env_vars", {})
        session_vars = context.get("session_vars", {})
        test_results = context.get("test_results", [])
        response_body = context.get("response_body")
        status_code = context.get("status_code", 0)
        response_headers = context.get("response_headers", {})

        # 模拟 pm 对象
        class MockPM:
            class Environment:
                @staticmethod
                def get(key):
                    return env_vars.get(key)

                @staticmethod
                def set(key, val):
                    env_vars[key] = val

                @staticmethod
                def unset(key):
                    env_vars.pop(key, None)

            class SessionVariables:
                @staticmethod
                def get(key):
                    return session_vars.get(key)

                @staticmethod
                def set(key, val):
                    session_vars[key] = val

            class Globals:
                @staticmethod
                def get(key):
                    return context.get("globals_to_save", {}).get(key)

                @staticmethod
                def set(key, val):
                    context.setdefault("globals_to_save", {})[key] = val

            class Response:
                @staticmethod
                def json():
                    if isinstance(response_body, (dict, list)):
                        return response_body
                    if isinstance(response_body, str):
                        try:
                            return json.loads(response_body)
                        except (json.JSONDecodeError, TypeError):
                            return None
                    return None

                @property
                def status(self):
                    return status_code

                @property
                def statusCode(self):
                    return status_code

                class Headers:
                    @staticmethod
                    def get(name):
                        for k, v in response_headers.items():
                            if k.lower() == name.lower():
                                return v
                        return None

                headers = Headers()

            @staticmethod
            def test(name, fn):
                try:
                    fn()
                    test_results.append({"name": name, "passed": True})
                except Exception as e:
                    test_results.append({"name": name, "passed": False, "error": str(e)})

            @staticmethod
            def expect(val):
                class ExpectChain:
                    class To:
                        @staticmethod
                        def equal(expected):
                            if val != expected:
                                raise AssertionError(f"Expected {expected}, got {val}")

                        @staticmethod
                        def include(s):
                            if str(s) not in str(val):
                                raise AssertionError(f"Not contains: {s}")

                    to = To()

                return ExpectChain()

        pm = MockPM()

        # 尝试执行 Python 化的代码
        safe_globals = {
            "pm": pm,
            "json": json,
            "print": print,
            "len": len,
            "int": int,
            "str": str,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        try:
            # 简单的 JS → Python 语法转换
            py_code = code.replace("var ", "").replace("let ", "").replace("const ", "")
            py_code = py_code.replace("function(", "lambda:")
            py_code = py_code.replace("pm.response.json()", "pm.Response.json()")
            py_code = py_code.replace("pm.environment.", "pm.Environment.")
            py_code = py_code.replace("pm.sessionVariables.", "pm.SessionVariables.")
            py_code = py_code.replace("pm.globals.", "pm.Globals.")
            py_code = py_code.replace("pm.test(", "pm.test(")
            # 只提取 pm.* 调用行
            for line in py_code.split("\n"):
                line = line.strip().rstrip(";")
                if not line or line.startswith("//") or line.startswith("/*"):
                    continue
                if "pm." in line:
                    try:
                        exec(line, safe_globals)
                    except Exception as line_err:
                        _logger.debug(f"Python模拟跳过行: {line} -> {line_err}")
        except Exception as e:
            _logger.warning(f"Python 模拟执行脚本异常: {e}")

        context["env_vars"] = env_vars
        context["session_vars"] = session_vars
        context["test_results"] = test_results
        return context


# ====================================================================
# Python 脚本引擎（对标 Apifox 后置脚本）
# ====================================================================


# 允许导入的安全模块白名单（其余一律拒绝，防止逃逸）
_PY_ALLOWED_IMPORTS = {
    "json", "re", "math", "datetime", "decimal", "collections", "itertools",
    "functools", "operator", "string", "uuid", "hashlib", "base64",
    "urllib.parse", "pprint", "statistics", "random", "copy",
}
# 明确禁止的高危模块（即便出现在白名单也二次拦截）
_PY_BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "shutil", "pathlib", "ctypes",
    "importlib", "builtins", "code", "codeop", "pty", "spawn", "platform",
    "multiprocessing", "threading", "pickle", "marshal", "asyncio",
    "tempfile", "signal", "resource", "fcntl", "glob", "linecache",
    "traceback", "types", "inspect", "builtins", "runpy", "webbrowser",
}


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    """受限的 __import__：仅允许白名单内的模块，禁止相对导入"""
    if level:
        raise ImportError("相对导入被禁止")
    top = (name or "").split(".")[0]
    if not top or top in _PY_BLOCKED_IMPORTS or top not in _PY_ALLOWED_IMPORTS:
        raise ImportError(f"导入模块 '{name}' 被禁止：仅允许安全模块")
    return __import__(name, globals, locals, fromlist, level)


# 模块级一次性检测 RestrictedPython 是否可用，避免在线程中反复 import 产生不确定行为
try:
    from RestrictedPython import compile_restricted_exec, safe_builtins as _RP_SAFE_BUILTINS  # type: ignore
    from RestrictedPython.Guards import safer_getattr as _RP_SAFER_GETATTR, guarded_setattr as _RP_GUARDED_SETATTR  # type: ignore
    _HAS_RESTRICTED_PYTHON = True
except ImportError:  # RestrictedPython 未安装时回退到 exec + 受限内建
    _HAS_RESTRICTED_PYTHON = False
    _RP_SAFE_BUILTINS = None
    _RP_SAFER_GETATTR = None
    _RP_GUARDED_SETATTR = None


# RestrictedPython 将 `i += 1` 转换为 `_inplacevar_('+=', i, 1)`，操作符以字符串传入
import operator as _operator

_PY_INPLACE_OPS = {
    "+=": _operator.iadd, "-=": _operator.isub, "*=": _operator.imul,
    "/=": _operator.itruediv, "//=": _operator.ifloordiv, "%=": _operator.imod,
    "**=": _operator.ipow, "<<=": _operator.ilshift, ">>=": _operator.irshift,
    "&=": _operator.iand, "|=": _operator.ior, "^=": _operator.ixor,
}


def _py_inplacevar(op: str, x: Any, y: Any) -> Any:
    """受限的增强赋值守卫：按字符串操作符映射到实际运算"""
    func = _PY_INPLACE_OPS.get(op)
    if func is None:
        raise ValueError(f"不支持的增强赋值操作符: {op}")
    return func(x, y)


@dataclass
class ScriptResult:
    """Python 脚本执行结果"""
    success: bool = True
    extracted_vars: Dict[str, Any] = field(default_factory=dict)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    persisted_globals: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class _PmResponse:
    """pm.response：响应对象"""

    def __init__(self, body: Any, status_code: int, headers: Dict[str, Any], elapsed_ms: int = 0):
        self._body = body
        self.status_code = status_code
        self.headers = dict(headers or {})
        self.elapsed_ms = elapsed_ms

    def json(self) -> Any:
        """解析响应体为 JSON"""
        if isinstance(self._body, (dict, list)):
            return self._body
        if isinstance(self._body, str):
            try:
                return json.loads(self._body)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @property
    def text(self) -> str:
        """响应文本"""
        if isinstance(self._body, str):
            return self._body
        try:
            return json.dumps(self._body, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(self._body)

    def get_header(self, name: str) -> Any:
        """按名称获取响应头（大小写不敏感）"""
        lower = (name or "").lower()
        for k, v in self.headers.items():
            if str(k).lower() == lower:
                return v
        return None


class _PmRequest:
    """pm.request：请求对象"""

    def __init__(self, method: str = "", url: str = "", headers: Optional[Dict[str, Any]] = None, body: Any = None):
        self.method = method
        self.url = url
        self.headers = dict(headers or {})
        self.body = body

    def get_header(self, name: str) -> Any:
        lower = (name or "").lower()
        for k, v in self.headers.items():
            if str(k).lower() == lower:
                return v
        return None


class _PmVarStore:
    """通用变量存储（get/set/unset/to_dict）"""

    def __init__(self, store: Dict[str, Any]):
        self._store = store

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def unset(self, key: str) -> None:
        self._store.pop(key, None)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._store)


class _PmGlobals(_PmVarStore):
    """pm.globals：全局变量（支持 persist 标记）"""

    def __init__(self, store: Dict[str, Any], persisted: Dict[str, Any]):
        super().__init__(store)
        self._persisted = persisted

    def persist(self, key: str) -> None:
        """将已 set 的全局变量标记为需要持久化到数据库"""
        if key in self._store:
            self._persisted[key] = self._store[key]


class _Expectation:
    """pm.expect(value) 返回的断言构建器：所有断言收集到列表，不抛异常"""

    def __init__(self, value: Any, assertions: List[Dict[str, Any]]):
        self._value = value
        self._assertions = assertions

    def _record(self, passed: bool, name: str, error: Optional[str] = None,
                expected: Any = None, actual: Any = None) -> None:
        self._assertions.append({
            "name": name,
            "passed": passed,
            "error": error,
            "expected": expected,
            "actual": actual,
        })

    def to_equal(self, expected: Any) -> "_Expectation":
        ok = self._value == expected
        self._record(ok, f"expect to_equal({expected!r})", None if ok else f"期望 {expected!r}，实际 {self._value!r}", expected, self._value)
        return self

    def to_not_equal(self, expected: Any) -> "_Expectation":
        ok = self._value != expected
        self._record(ok, f"expect to_not_equal({expected!r})", None if ok else f"不应等于 {expected!r}", expected, self._value)
        return self

    # 别名
    not_to_equal = to_not_equal

    def to_be_truthy(self) -> "_Expectation":
        ok = bool(self._value)
        self._record(ok, "expect to_be_truthy", None if ok else f"期望真值，实际 {self._value!r}", None, self._value)
        return self

    def to_be_falsy(self) -> "_Expectation":
        ok = not bool(self._value)
        self._record(ok, "expect to_be_falsy", None if ok else f"期望假值，实际 {self._value!r}", None, self._value)
        return self

    def to_be_none(self) -> "_Expectation":
        ok = self._value is None
        self._record(ok, "expect to_be_none", None if ok else f"期望 None，实际 {self._value!r}", None, self._value)
        return self

    def to_contain(self, item: Any) -> "_Expectation":
        try:
            ok = item in self._value
        except TypeError:
            ok = False
        self._record(ok, f"expect to_contain({item!r})", None if ok else f"未包含 {item!r}", item, self._value)
        return self

    # 别名
    to_include = to_contain

    def to_match_regex(self, pattern: str) -> "_Expectation":
        try:
            ok = re.search(pattern, str(self._value)) is not None
        except re.error as e:
            ok = False
            self._record(False, f"expect to_match_regex({pattern!r})", f"正则表达式无效: {e}", pattern, self._value)
            return self
        self._record(ok, f"expect to_match_regex({pattern!r})", None if ok else f"不匹配正则 {pattern!r}", pattern, self._value)
        return self

    def to_be_a(self, type_name: str) -> "_Expectation":
        _type_map = {"str": str, "string": str, "int": int, "integer": int,
                     "float": float, "bool": bool, "boolean": bool,
                     "list": list, "dict": dict, "map": dict, "set": set}
        py_type = _type_map.get((type_name or "").lower())
        if py_type is None:
            self._record(False, f"expect to_be_a({type_name!r})", f"未知类型 {type_name!r}", type_name, type(self._value).__name__)
            return self
        ok = isinstance(self._value, py_type)
        self._record(ok, f"expect to_be_a({type_name!r})", None if ok else f"期望类型 {type_name!r}，实际 {type(self._value).__name__}", type_name, type(self._value).__name__)
        return self

    to_be_instance_of = to_be_a

    def to_be_greater_than(self, n: Any) -> "_Expectation":
        try:
            ok = self._value > n
        except TypeError:
            ok = False
        self._record(ok, f"expect to_be_greater_than({n!r})", None if ok else f"期望大于 {n!r}，实际 {self._value!r}", n, self._value)
        return self

    to_be_above = to_be_greater_than

    def to_be_less_than(self, n: Any) -> "_Expectation":
        try:
            ok = self._value < n
        except TypeError:
            ok = False
        self._record(ok, f"expect to_be_less_than({n!r})", None if ok else f"期望小于 {n!r}，实际 {self._value!r}", n, self._value)
        return self

    to_be_below = to_be_less_than

    def to_have_key(self, key: Any) -> "_Expectation":
        try:
            ok = key in self._value
        except TypeError:
            ok = False
        self._record(ok, f"expect to_have_key({key!r})", None if ok else f"不存在键 {key!r}", key, None)
        return self

    def to_start_with(self, prefix: str) -> "_Expectation":
        try:
            ok = str(self._value).startswith(prefix)
        except Exception:
            ok = False
        self._record(ok, f"expect to_start_with({prefix!r})", None if ok else f"不以 {prefix!r} 开头", prefix, self._value)
        return self

    def to_end_with(self, suffix: str) -> "_Expectation":
        try:
            ok = str(self._value).endswith(suffix)
        except Exception:
            ok = False
        self._record(ok, f"expect to_end_with({suffix!r})", None if ok else f"不以 {suffix!r} 结尾", suffix, self._value)
        return self


class PmPython:
    """
    Python 脚本的 pm 对象，提供与 JS 对等的 Pythonic API：
    - pm.response / pm.request
    - pm.variables / pm.environment / pm.globals
    - pm.expect(value) 断言收集
    - pm.extract(name, json_path, from_body=True) 提取变量
    - pm.test(name, fn) 测试块
    """

    @property
    def _context(self):
        raise AttributeError("禁止访问属性 '_context'")

    def __init__(self, context: Dict[str, Any]):
        self._internal_context = context
        # 断言与测试结果统一收集到 test_results，便于执行引擎合并计数
        self._assertions: List[Dict[str, Any]] = context.setdefault("test_results", [])
        env_vars = context.setdefault("env_vars", {})
        session_vars = context.setdefault("session_vars", {})
        globals_store = context.setdefault("globals_to_save", {})
        # persisted_globals 单独存放，最终写入 ScriptResult.persisted_globals
        self._persisted_globals = context.setdefault("persisted_globals", {})

        self.response = _PmResponse(
            body=context.get("response_body"),
            status_code=context.get("status_code", 0),
            headers=context.get("response_headers", {}) or {},
            elapsed_ms=context.get("elapsed_ms", 0),
        )
        self.request = _PmRequest(
            method=context.get("request_method", ""),
            url=context.get("request_url", ""),
            headers=context.get("request_headers", {}) or {},
            body=context.get("request_body"),
        )
        self.environment = _PmVarStore(env_vars)
        self.variables = _PmVarStore(session_vars)
        self.sessionVariables = _PmVarStore(session_vars)
        self.globals = _PmGlobals(globals_store, self._persisted_globals)

    def expect(self, value: Any) -> _Expectation:
        """断言：返回构建器，所有断言收集到列表，不抛异常"""
        return _Expectation(value, self._assertions)

    def extract(self, name: str, json_path: str, from_body: bool = True) -> Any:
        """
        提取变量。from_body=True 时从响应体按 JSONPath 提取（复用项目内置解析器）。
        提取结果写入 pm.variables（session_vars）与 extracted_vars。
        """
        from fastapi_backend.utils.autotest_helpers import extract_jsonpath_value

        source = self.response.json() if from_body else self._internal_context.get("response_body")
        try:
            value = extract_jsonpath_value(source, json_path)
        except Exception as e:
            _logger.warning(f"pm.extract 提取失败 ({json_path}): {e}")
            value = None
        self.variables.set(name, value)
        self._internal_context.setdefault("extracted_vars", {})[name] = value
        return value

    def test(self, name: str, fn) -> None:
        """测试块：捕获异常并记录通过/失败"""
        try:
            fn()
            self._assertions.append({"name": name, "passed": True})
        except Exception as e:
            self._assertions.append({"name": name, "passed": False, "error": str(e)})


class PythonScriptEngine:
    """Python 脚本执行引擎（RestrictedPython 沙箱 + 超时控制）"""

    DEFAULT_TIMEOUT = 10  # 默认执行超时（秒）

    @staticmethod
    def execute(script: str, context: Dict[str, Any], timeout: Optional[int] = None) -> ScriptResult:
        """
        执行 Python 脚本。
        - 使用 RestrictedPython 编译并限制内建函数，禁止危险 import
        - 在独立线程中执行，超时（默认 10s）后返回错误结果
        - 捕获所有异常，转换为 ScriptResult.error
        - pm.expect 断言收集到 assertions（不抛异常）
        """
        if not script or not str(script).strip():
            return ScriptResult(success=True)

        timeout = timeout if timeout is not None else PythonScriptEngine.DEFAULT_TIMEOUT
        pm = PmPython(context)

        # 容器：捕获执行期异常与日志
        holder: Dict[str, Any] = {"error": None, "logs": []}

        def _safe_print(*args, **kwargs):
            holder["logs"].append(" ".join(str(a) for a in args))

        def _run():
            try:
                PythonScriptEngine._exec_restricted(script, pm, _safe_print)
            except Exception as e:  # noqa: BLE001 - 沙箱需捕获所有异常
                holder["error"] = f"{type(e).__name__}: {e}"

        thread = threading.Thread(target=_run, name="pm-python-script", daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            # 超时：线程为 daemon，无法强制终止（Windows 限制），返回超时错误
            err = f"脚本执行超时（>{timeout}s）"
            _logger.warning(err)
            return ScriptResult(
                success=False,
                extracted_vars=context.get("extracted_vars", {}),
                assertions=list(context.get("test_results", [])),
                persisted_globals=context.get("persisted_globals", {}),
                error=err,
            )

        error = holder.get("error")
        assertions = list(context.get("test_results", []))
        extracted = context.get("extracted_vars", {})
        persisted = context.get("persisted_globals", {})
        # 若脚本中显式 pm.globals.persist，则持久化全集；否则 persisted_globals 与 globals_to_save 保持一致
        if not persisted and context.get("globals_to_save"):
            persisted = dict(context.get("globals_to_save", {}))

        return ScriptResult(
            success=error is None,
            extracted_vars=extracted,
            assertions=assertions,
            persisted_globals=persisted,
            error=error,
        )

    @staticmethod
    def run_as_context(code: str, context: Dict[str, Any], phase: str = "pre") -> Dict[str, Any]:
        """
        执行 Python 脚本并将结果回写到 context（与 JS 引擎签名对齐）。
        执行引擎统一通过 context 读取：env_vars/session_vars/test_results/globals_to_save。
        """
        result = PythonScriptEngine.execute(code, context)
        # 确保关键键存在，便于上游安全读取
        context.setdefault("env_vars", {})
        context.setdefault("session_vars", {})
        context.setdefault("test_results", [])
        context.setdefault("globals_to_save", {})
        context["extracted_vars"] = result.extracted_vars
        context["assertions"] = result.assertions
        context["python_success"] = result.success
        context["python_language"] = "python"
        if result.error:
            context["python_error"] = result.error
            _logger.warning(f"Python {phase} 脚本执行失败: {result.error}")
        return context

    @staticmethod
    def _exec_restricted(script: str, pm: PmPython, print_fn) -> None:
        """
        使用 RestrictedPython 编译并执行脚本（模块级已检测可用性）。
        若 RestrictedPython 未安装，回退到 exec + 受限内建函数方案（保护较弱，见注释）。
        """
        # 受限内建：以 RestrictedPython 的 safe_builtins 为基础（已剔除危险函数），
        # 再补充脚本常用且安全的内建与受控导入
        base_builtins = dict(_RP_SAFE_BUILTINS) if _HAS_RESTRICTED_PYTHON else {}
        safe_builtins = {
            **base_builtins,
            "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
            "enumerate": enumerate, "filter": filter, "float": float,
            "hash": hash, "int": int, "isinstance": isinstance, "len": len,
            "list": list, "map": map, "max": max, "min": min, "print": print_fn,
            "range": range, "round": round, "set": set, "sorted": sorted,
            "str": str, "sum": sum, "tuple": tuple, "type": type, "zip": zip,
            "True": True, "False": False, "None": None,
            "repr": repr, "frozenset": frozenset, "format": format,
            "reversed": reversed, "bytes": bytes, "chr": chr, "ord": ord,
            "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
            "KeyError": KeyError, "IndexError": IndexError, "AttributeError": AttributeError,
            "AssertionError": AssertionError, "StopIteration": StopIteration,
            "ZeroDivisionError": ZeroDivisionError, "NameError": NameError,
            # 受控导入：仅白名单模块
            "__import__": _guarded_import,
        }
        # 显式移除可被滥用的内建（双保险）
        for _bad in ("eval", "exec", "compile", "open", "input", "globals",
                     "locals", "vars", "dir", "breakpoint", "memoryview"):
            safe_builtins.pop(_bad, None)

        user_globals: Dict[str, Any] = {
            "__builtins__": safe_builtins,
            "__name__": "pm_python_sandbox",
            "pm": pm,
            "json": json,
            "re": re,
            "print": print_fn,
            # 守卫：受限属性/项访问与增强赋值
            "_getitem_": lambda obj, key: obj[key],
            "_write_": lambda obj: obj,
            "_inplacevar_": _py_inplacevar,
            "_apply_": lambda func, *args, **kwargs: func(*args, **kwargs),
        }
        if _HAS_RESTRICTED_PYTHON:
            user_globals["_getattr_"] = _RP_SAFER_GETATTR
            user_globals["_setattr_"] = _RP_GUARDED_SETATTR
        else:
            # 回退方案：自实现 _getattr_ 拦截下划线属性访问
            def _safe_getattr(obj, name):
                if isinstance(name, str) and name.startswith("_"):
                    raise AttributeError(f"禁止访问属性 '{name}'")
                return getattr(obj, name)
            user_globals["_getattr_"] = _safe_getattr
            user_globals["_setattr_"] = lambda obj, name, value: setattr(obj, name, value)

        if _HAS_RESTRICTED_PYTHON:
            # RestrictedPython 编译：改写属性访问/写入以接入守卫，并返回编译错误
            result = compile_restricted_exec(script, filename="<pm-python-script>")
            if result.errors:
                raise SyntaxError("；".join(str(e) for e in result.errors))
            exec(result.code, user_globals)  # noqa: S102 - 受限字节码执行
        else:
            # 回退方案：RestrictedPython 未安装，使用 exec + 受限内建函数。
            # 注意：此方案对属性访问的保护弱于 RestrictedPython，依赖 __import__ 拦截危险模块。
            _logger.warning("RestrictedPython 未安装，回退到 exec + 受限内建函数方案（保护较弱）")
            try:
                bytecode = compile(script, filename="<pm-python-script>", mode="exec")
            except SyntaxError as e:
                raise SyntaxError(f"脚本语法错误: {e.msg} (行 {e.lineno})") from None
            exec(bytecode, user_globals)  # noqa: S102 - 受限内建执行
