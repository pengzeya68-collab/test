# -*- coding: utf-8 -*-
"""
Python 脚本引擎单元测试

覆盖：
- pm.variables / pm.environment / pm.globals 变量操作
- pm.response.json()/status_code/headers/text 访问
- pm.expect 断言通过/失败收集
- pm.extract JSONPath 提取
- pm.test 测试块
- 危险操作拦截（import os / __import__ subprocess / 下划线属性）
- 超时处理
- 语法错误处理
- ScriptEngine 按语言分派
- run_as_context 上下文回写
"""
import os
import sys

# 确保项目根目录在 PYTHONPATH 中（兼容直接 pytest 调用）
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest

from fastapi_backend.services.script_engine import (
    PythonScriptEngine,
    ScriptEngine,
    ScriptResult,
    _HAS_RESTRICTED_PYTHON,
)


# ========== 辅助函数 ==========


def _make_ctx(body=None, status_code=200, headers=None, **extra):
    """构建脚本上下文"""
    ctx = {
        "env_vars": {},
        "session_vars": {},
        "user_id": 1,
        "response_body": body,
        "status_code": status_code,
        "response_headers": headers or {"Content-Type": "application/json"},
    }
    ctx.update(extra)
    return ctx


def _exec(script: str, ctx=None, timeout=None):
    """便捷执行入口"""
    return PythonScriptEngine.execute(script, ctx if ctx is not None else _make_ctx(), timeout=timeout)


# ========== 变量操作 ==========


def test_variables_set_and_get():
    """pm.variables 的 set/get/unset/to_dict"""
    ctx = _make_ctx()
    script = '''
pm.variables.set("name", "tester")
pm.variables.set("count", 3)
pm.environment.set("env", "prod")
'''
    r = _exec(script, ctx)
    assert r.success is True
    assert r.error is None
    assert ctx["session_vars"]["name"] == "tester"
    assert ctx["session_vars"]["count"] == 3
    assert ctx["env_vars"]["env"] == "prod"


def test_variables_get_returns_default():
    """pm.variables.get 取不存在的键返回 None"""
    ctx = _make_ctx()
    script = '''
val = pm.variables.get("not_exist")
pm.variables.set("result", val)
'''
    r = _exec(script, ctx)
    assert r.success is True
    assert ctx["session_vars"]["result"] is None


def test_globals_set_and_persist():
    """pm.globals.set + persist 标记"""
    ctx = _make_ctx()
    script = '''
pm.globals.set("token", "abc123")
pm.globals.persist("token")
pm.globals.set("temp", "x")
'''
    r = _exec(script, ctx)
    assert r.success is True
    assert r.persisted_globals.get("token") == "abc123"
    # 未 persist 的全局变量仍会出现在持久化集合中（回写 globals_to_save）
    assert "temp" in ctx["globals_to_save"]


# ========== 响应访问 ==========


def test_response_json_access():
    """pm.response.json() / status_code / headers / text"""
    body = {"code": 0, "data": {"token": "abc", "id": 42}}
    ctx = _make_ctx(body=body, status_code=200, headers={"Content-Type": "application/json", "X-Trace": "t1"})
    script = '''
body = pm.response.json()
status = pm.response.status_code
ct = pm.response.get_header("content-type")
trace = pm.response.get_header("X-Trace")
text = pm.response.text
pm.variables.set("token", body["data"]["token"])
pm.variables.set("status", status)
pm.variables.set("ct", ct)
pm.variables.set("trace", trace)
pm.variables.set("text_len", len(text))
'''
    r = _exec(script, ctx)
    assert r.success is True, r.error
    assert ctx["session_vars"]["token"] == "abc"
    assert ctx["session_vars"]["status"] == 200
    assert ctx["session_vars"]["ct"] == "application/json"
    assert ctx["session_vars"]["trace"] == "t1"
    assert ctx["session_vars"]["text_len"] > 0


def test_response_json_from_string_body():
    """响应体为字符串时 pm.response.json() 自动解析"""
    ctx = _make_ctx(body='{"code": 1, "msg": "ok"}', status_code=201)
    script = '''
body = pm.response.json()
pm.variables.set("code", body["code"])
pm.variables.set("status", pm.response.status_code)
'''
    r = _exec(script, ctx)
    assert r.success is True, r.error
    assert ctx["session_vars"]["code"] == 1
    assert ctx["session_vars"]["status"] == 201


# ========== 断言 ==========


def test_expect_pass():
    """pm.expect 断言全部通过"""
    ctx = _make_ctx(body={"code": 0, "list": [1, 2, 3]}, status_code=200)
    script = '''
status = pm.response.status_code
body = pm.response.json()
pm.expect(status).to_equal(200)
pm.expect(body["code"]).to_equal(0)
pm.expect(body["list"]).to_contain(2)
pm.expect(body).to_have_key("code")
pm.expect("hello world").to_match_regex(r"hello")
pm.expect(body["list"]).to_be_truthy()
pm.expect(5).to_be_greater_than(3)
pm.expect("abc").to_start_with("ab")
'''
    r = _exec(script, ctx)
    assert r.success is True, r.error
    assert len(r.assertions) == 8
    assert all(a["passed"] for a in r.assertions), r.assertions


def test_expect_fail_recorded_not_raised():
    """失败的断言被记录但不抛异常，脚本继续执行"""
    ctx = _make_ctx(body={"code": 1}, status_code=500)
    script = '''
pm.expect(pm.response.status_code).to_equal(200)
pm.expect(pm.response.json()["code"]).to_equal(0)
pm.variables.set("after_assert", "reached")
'''
    r = _exec(script, ctx)
    # 断言失败不影响脚本完成（success 取决于是否抛异常，而非断言）
    assert r.success is True
    assert r.error is None
    failed = [a for a in r.assertions if not a["passed"]]
    assert len(failed) == 2
    assert ctx["session_vars"]["after_assert"] == "reached"


def test_pm_test_block_pass_and_fail():
    """pm.test 测试块：通过/失败均被收集"""
    ctx = _make_ctx(body={"v": 10})
    script = '''
def test_ok():
    assert pm.response.json()["v"] == 10

def test_fail():
    assert pm.response.json()["v"] == 99, "值不匹配"

pm.test("正常用例", test_ok)
pm.test("失败用例", test_fail)
'''
    r = _exec(script, ctx)
    assert r.success is True
    names = {a["name"]: a["passed"] for a in r.assertions}
    assert names.get("正常用例") is True
    assert names.get("失败用例") is False


# ========== 提取 ==========


def test_extract_from_body():
    """pm.extract 按 JSONPath 从响应体提取"""
    ctx = _make_ctx(body={"data": {"id": 42, "items": [{"name": "a"}, {"name": "b"}]}})
    script = '''
pm.extract("user_id", "$.data.id", from_body=True)
pm.extract("first_name", "$.data.items[0].name", from_body=True)
'''
    r = _exec(script, ctx)
    assert r.success is True, r.error
    assert r.extracted_vars["user_id"] == 42
    assert r.extracted_vars["first_name"] == "a"
    # 提取结果同时写入 session_vars 供后续步骤使用
    assert ctx["session_vars"]["user_id"] == 42


# ========== 安全：危险操作拦截 ==========


def test_import_os_blocked():
    """import os 被拦截"""
    r = _exec("import os\nos.listdir('/')")
    assert r.success is False
    assert r.error is not None
    assert "os" in r.error or "禁止" in r.error or "import" in r.error.lower()


def test_dunder_import_subprocess_blocked():
    """__import__('subprocess') 被拦截"""
    r = _exec("m = __import__('subprocess')")
    assert r.success is False
    assert r.error is not None


def test_dunder_attribute_access_blocked():
    """下划线属性访问被拦截（防止逃逸）"""
    r = _exec("x = pm._context")
    assert r.success is False
    assert r.error is not None


def test_allowed_import_json_works():
    """白名单模块（json）可正常导入并使用"""
    ctx = _make_ctx()
    script = '''
import json
pm.variables.set("serialized", json.dumps({"a": 1}))
'''
    r = _exec(script, ctx)
    assert r.success is True, r.error
    assert ctx["session_vars"]["serialized"] == '{"a": 1}'


# ========== 超时与语法错误 ==========


def test_timeout_handling():
    """无限循环触发超时"""
    r = _exec("i = 0\nwhile True:\n    i += 1", timeout=2)
    assert r.success is False
    assert r.error is not None
    assert "超时" in r.error


def test_syntax_error_handling():
    """语法错误被捕获并报告"""
    r = _exec("def broken(:\n    pass")
    assert r.success is False
    assert r.error is not None
    assert "SyntaxError" in r.error or "syntax" in r.error.lower() or "语法" in r.error


def test_empty_script_returns_success():
    """空脚本返回成功"""
    r = _exec("")
    assert r.success is True
    assert r.error is None
    assert r.assertions == []


# ========== 集成：分派与上下文回写 ==========


def test_run_as_context_writes_keys():
    """run_as_context 将结果回写到 context 的标准键"""
    ctx = _make_ctx(body={"code": 0, "data": {"id": 7}})
    script = '''
pm.expect(pm.response.json()["code"]).to_equal(0)
pm.extract("uid", "$.data.id")
pm.globals.set("g", "v")
pm.variables.set("s", "1")
pm.environment.set("e", "2")
'''
    out = PythonScriptEngine.run_as_context(script, ctx, phase="post")
    assert out is ctx
    assert out["python_language"] == "python"
    assert out["python_success"] is True
    assert out["extracted_vars"]["uid"] == 7
    assert out["session_vars"]["s"] == "1"
    assert out["env_vars"]["e"] == "2"
    assert out["globals_to_save"]["g"] == "v"
    assert len(out["assertions"]) == 1
    assert out["assertions"][0]["passed"] is True


def test_script_engine_dispatch_to_python():
    """ScriptEngine.run_pre_script(language='python') 路由到 Python 引擎"""
    ctx = _make_ctx()
    script = 'pm.variables.set("dispatched", "python")'
    ScriptEngine.run_pre_script(script, ctx, language="python")
    assert ctx.get("python_language") == "python"
    assert ctx["session_vars"]["dispatched"] == "python"


def test_script_engine_dispatch_default_is_js():
    """默认语言（javascript）不触发 Python 引擎标记"""
    ctx = _make_ctx()
    # 一个简单的 JS 风格脚本；dukpy 不可用时会回退到 Python 模拟，但不应崩溃
    ScriptEngine.run_pre_script("pm.environment.set('k', 'v')", ctx, language="javascript")
    # python_language 标记不应出现（说明走了 JS 路径）
    assert ctx.get("python_language") is None


def test_script_engine_dispatch_post_python():
    """ScriptEngine.run_post_script(language='python') 路由到 Python 引擎"""
    ctx = _make_ctx(body={"code": 0}, status_code=200)
    script = '''
pm.expect(pm.response.status_code).to_equal(200)
pm.variables.set("done", True)
'''
    ScriptEngine.run_post_script(script, ctx, language="python")
    assert ctx.get("python_language") == "python"
    assert ctx["session_vars"]["done"] is True
    assert ctx["assertions"][0]["passed"] is True


# ========== RestrictedPython 可用性（环境校验）==========


@pytest.mark.skipif(not _HAS_RESTRICTED_PYTHON, reason="RestrictedPython 未安装，跳过强沙箱专属测试")
def test_restricted_python_active():
    """RestrictedPython 已安装并启用（强沙箱路径）"""
    # 在强沙箱下，__import__ 作为下划线名称在编译期被拒（SyntaxError）
    r = _exec("m = __import__('subprocess')")
    assert r.success is False
    assert "SyntaxError" in r.error or "invalid" in r.error.lower()
