"""
JavaScript 脚本引擎

提供 pm.* API 兼容层，支持前置/后置脚本执行。
复用现有变量系统（context_vars, session_vars, global_vars）。
"""
import json
import logging
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
    def run_pre_script(code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行前置脚本"""
        return ScriptEngine._execute_script(code, context, phase="pre")

    @staticmethod
    def run_post_script(code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行后置脚本"""
        return ScriptEngine._execute_script(code, context, phase="post")

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
        test_results = []
        globals_to_save = {}

        # 构建 pm 对象的 JS 代码
        pm_bridge = f"""
var pm = {{
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
        _body: {json.dumps(context.get('response_body'), ensure_ascii=False) if context.get('response_body') is not None else 'null'},
        _status: {context.get('status_code', 0)},
        _headers: {json.dumps(context.get('response_headers', {}), ensure_ascii=False)},
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
            _h: {json.dumps(context.get('response_headers', {}), ensure_ascii=False)},
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
        result_code = "JSON.stringify({env: pm.environment._data, session: pm.sessionVariables._data, tests: __test_results, globals: __globals_to_save})"
        full_code = pm_bridge + "\n" + code + ";\n" + result_code

        # 单次执行，通过返回值获取结果
        result_str = dukpy.evaljs(full_code)

        try:
            result_data = json.loads(result_str) if isinstance(result_str, str) else {}
        except (json.JSONDecodeError, TypeError):
            result_data = {}

        context["env_vars"] = result_data.get("env", env_vars)
        context["session_vars"] = result_data.get("session", session_vars)
        context["test_results"] = result_data.get("tests", [])
        context["globals_to_save"] = result_data.get("globals", {})

        return context

    @staticmethod
    def _execute_with_python(code: str, context: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """
        Python 模拟执行：解析常见的 pm.* API 调用。
        当 dukpy 不可用时的回退方案。
        """
        import re

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
        safe_globals = {"pm": pm, "json": json, "print": print, "len": len, "int": int, "str": str, "float": float, "bool": bool, "list": list, "dict": dict}
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
