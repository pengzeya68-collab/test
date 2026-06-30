"""
JSON Schema 断言功能测试

测试 fastapi_backend/services/autotest_assertion_engine.py 中的 json_schema target 类型断言，
对标 Apifox 的 JSON Schema 断言能力。覆盖：
1. 简单对象 schema 验证通过
2. 简单对象 schema 验证失败（类型不匹配）
3. 嵌套对象 schema
4. 数组 schema
5. required 字段缺失
6. 响应体非 JSON 时的处理
7. schema 格式错误时的处理
8. matches / not_matches 操作符
9. expected_schema / expected / expectedValue 字段兼容
10. 与 status_code 断言混合
11. 旧版 json_schema 操作符回归
"""

import json

from fastapi_backend.services.autotest_assertion_engine import (
    _handle_json_schema_target,
    _validate_json_schema_detailed,
    execute_assertions,
)


# ========== 单元测试：_validate_json_schema_detailed ==========


class TestValidateJsonSchemaDetailed:
    """直接测试详细校验函数的返回值与错误路径格式"""

    def test_simple_object_passes(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        passed, err = _validate_json_schema_detailed({"name": "alice"}, schema)
        assert passed is True
        assert err is None

    def test_type_mismatch_returns_field_path(self):
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "required": ["age"],
        }
        passed, err = _validate_json_schema_detailed({"age": "not a number"}, schema)
        assert passed is False
        assert err is not None
        assert "Schema 验证失败" in err
        assert "age" in err  # 字段路径
        assert "is not of type" in err  # 错误原因

    def test_nested_object_path(self):
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {"name": {"type": "integer"}},
                        }
                    },
                }
            },
        }
        passed, err = _validate_json_schema_detailed({"data": {"user": {"name": "x"}}}, schema)
        assert passed is False
        assert err is not None
        assert "data.user.name" in err  # 嵌套路径

    def test_array_item_path(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        }
        passed, err = _validate_json_schema_detailed([{"id": 1}, {"id": "x"}], schema)
        assert passed is False
        assert err is not None
        assert "[1].id" in err  # 数组索引路径
        assert "is not of type" in err

    def test_required_missing_reports_root_path(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name", "age"],
        }
        passed, err = _validate_json_schema_detailed({"name": "test"}, schema)
        assert passed is False
        assert err is not None
        assert "(根)" in err  # required 缺失在根级报告
        assert "is a required property" in err

    def test_empty_schema_passes(self):
        passed, err = _validate_json_schema_detailed({"anything": 1}, {})
        assert passed is True
        assert err is None

    def test_none_schema_passes(self):
        passed, err = _validate_json_schema_detailed({"anything": 1}, None)
        assert passed is True
        assert err is None

    def test_schema_not_dict_returns_format_error(self):
        passed, err = _validate_json_schema_detailed({"a": 1}, [1, 2, 3])
        assert passed is False
        assert "schema 必须为对象" in err

    def test_invalid_schema_format_raises_schema_error(self):
        # type 关键字取非法值，应触发 SchemaError 并返回“Schema 格式错误”
        schema = {"type": "not_a_real_type"}
        passed, err = _validate_json_schema_detailed({"a": 1}, schema)
        assert passed is False
        assert "Schema 格式错误" in err

    def test_schema_as_json_string(self):
        schema_str = json.dumps({"type": "object", "required": ["x"]})
        passed, err = _validate_json_schema_detailed({"x": 1}, schema_str)
        assert passed is True
        assert err is None

    def test_invalid_json_string_schema(self):
        passed, err = _validate_json_schema_detailed({"a": 1}, "{not valid json")
        assert passed is False
        assert "不是合法的 JSON 字符串" in err

    def test_root_type_mismatch(self):
        # 整体类型不符（响应为字符串，schema 期望对象）
        passed, err = _validate_json_schema_detailed("a string", {"type": "object"})
        assert passed is False
        assert "(根)" in err
        assert "is not of type" in err


# ========== 集成测试：execute_assertions（数组格式） ==========


class TestExecuteAssertionsJsonSchema:
    """通过 execute_assertions 入口测试 json_schema target 断言"""

    def _run(self, rules, response_body, status_code=200):
        return execute_assertions(rules, status_code, response_body, 0, {})

    def test_matches_passes(self):
        schema = {"type": "object", "properties": {"code": {"type": "integer"}}, "required": ["code"]}
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, {"code": 200, "msg": "ok"})
        assert result["passed"] is True
        detail = result["details"][0]
        assert detail["type"] == "json_schema"
        assert detail["operator"] == "matches"
        assert detail["passed"] is True
        assert detail["expected"] == schema

    def test_matches_fails_with_detailed_message(self):
        schema = {"type": "object", "properties": {"code": {"type": "integer"}}, "required": ["code"]}
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, {"code": "not_int"})
        assert result["passed"] is False
        assert "Schema 验证失败" in result["message"]
        assert "code" in result["message"]
        detail = result["details"][0]
        assert detail["passed"] is False
        assert "is not of type" in detail["message"]

    def test_not_matches_passes_when_schema_fails(self):
        # 响应不符合 schema -> not_matches 应通过
        schema = {"type": "object", "properties": {"code": {"type": "integer"}}, "required": ["code"]}
        rules = [{"target": "json_schema", "operator": "not_matches", "expected_schema": schema}]
        result = self._run(rules, {"unexpected": 1})
        assert result["passed"] is True
        detail = result["details"][0]
        assert detail["operator"] == "not_matches"
        assert detail["passed"] is True

    def test_not_matches_fails_when_schema_matches(self):
        # 响应符合 schema -> not_matches 应失败
        schema = {"type": "object", "properties": {"code": {"type": "integer"}}, "required": ["code"]}
        rules = [{"target": "json_schema", "operator": "not_matches", "expected_schema": schema}]
        result = self._run(rules, {"code": 200})
        assert result["passed"] is False

    def test_nested_schema_matches(self):
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                        "required": ["id", "name"],
                    },
                }
            },
            "required": ["data"],
        }
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, {"data": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]})
        assert result["passed"] is True

    def test_nested_schema_fails_with_path(self):
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {"user": {"type": "object", "properties": {"age": {"type": "integer"}}}},
                }
            },
        }
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, {"data": {"user": {"age": "x"}}})
        assert result["passed"] is False
        assert "data.user.age" in result["message"]

    def test_array_schema_fails(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        }
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, [{"id": 1}, {"id": "bad"}])
        assert result["passed"] is False
        assert "[1].id" in result["message"]

    def test_required_missing_fails(self):
        schema = {"type": "object", "required": ["token"]}
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, {"user": "alice"})
        assert result["passed"] is False
        assert "is a required property" in result["message"]
        assert "token" in result["message"]

    def test_non_json_response_matches_fails(self):
        schema = {"type": "object", "required": ["x"]}
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, "<html>not a json</html>")
        assert result["passed"] is False
        assert "非 JSON" in result["message"]

    def test_non_json_response_not_matches_passes(self):
        schema = {"type": "object", "required": ["x"]}
        rules = [{"target": "json_schema", "operator": "not_matches", "expected_schema": schema}]
        result = self._run(rules, "plain text response")
        assert result["passed"] is True

    def test_invalid_schema_format_handled(self):
        rules = [
            {"target": "json_schema", "operator": "matches", "expected_schema": {"type": "fake_type"}}
        ]
        result = self._run(rules, {"a": 1})
        assert result["passed"] is False
        assert "Schema 格式错误" in result["message"]

    def test_expected_value_fallback(self):
        # 未提供 expected_schema 时回退到 expected
        schema = {"type": "object", "required": ["code"]}
        rules = [{"target": "json_schema", "operator": "matches", "expected": schema}]
        result = self._run(rules, {"code": 1})
        assert result["passed"] is True

    def test_expected_value_fallback_camel(self):
        # 回退到 expectedValue
        schema = {"type": "object", "required": ["code"]}
        rules = [{"target": "json_schema", "operator": "matches", "expectedValue": schema}]
        result = self._run(rules, {"code": 1})
        assert result["passed"] is True

    def test_json_string_response_parsed(self):
        # 响应体为合法 JSON 字符串时应被解析后校验
        schema = {"type": "object", "required": ["code"]}
        rules = [{"target": "json_schema", "operator": "matches", "expected_schema": schema}]
        result = self._run(rules, '{"code": 200}')
        assert result["passed"] is True

    def test_mixed_rules_status_and_schema(self):
        # 与 status_code 断言混合执行
        schema = {"type": "object", "required": ["code"]}
        rules = [
            {"target": "status_code", "operator": "==", "expected": 200},
            {"target": "json_schema", "operator": "matches", "expected_schema": schema},
        ]
        result = self._run(rules, {"code": 200})
        assert result["passed"] is True
        assert result["has_status_code_assertion"] is True
        assert len(result["details"]) == 2
        types = [d["type"] for d in result["details"]]
        assert "status_code" not in types  # status_code 走 assertion 类型分支
        assert "assertion" in types
        assert "json_schema" in types

    def test_mixed_rules_schema_failure_propagates(self):
        # schema 断言失败时整体 passed=False，且不影响其它断言
        schema = {"type": "object", "required": ["code"]}
        rules = [
            {"target": "status_code", "operator": "==", "expected": 200},
            {"target": "json_schema", "operator": "matches", "expected_schema": schema},
        ]
        result = self._run(rules, {"no_code": 1})
        assert result["passed"] is False
        assert "Schema 验证失败" in result["message"]


# ========== 直接测试 _handle_json_schema_target ==========


class TestHandleJsonSchemaTarget:
    def test_returns_detail_structure(self):
        schema = {"type": "object", "required": ["a"]}
        res = _handle_json_schema_target(
            {"target": "json_schema", "operator": "matches", "expected_schema": schema},
            {"a": 1},
        )
        assert res["passed"] is True
        assert res["message"] is None
        assert res["detail"]["type"] == "json_schema"
        assert res["detail"]["field"] == "json_schema"
        assert res["detail"]["expected"] == schema
        assert res["detail"]["actual"] == {"a": 1}

    def test_not_match_operator_alias(self):
        # not_match 别名也应被识别为 not_matches 语义
        schema = {"type": "object", "required": ["a"]}
        res = _handle_json_schema_target(
            {"target": "json_schema", "operator": "not_match", "expected_schema": schema},
            {"missing": 1},
        )
        assert res["passed"] is True  # 不符合 schema -> not_match 通过


# ========== 旧版 json_schema 操作符回归 ==========


class TestJsonSchemaOperatorRegression:
    """确保新增 target 类型后，旧版 json_schema 操作符仍可用"""

    def test_json_schema_operator_via_body_target(self):
        schema = {"type": "object", "required": ["code"]}
        rules = [{"target": "body", "operator": "json_schema", "expected": schema}]
        result = execute_assertions(rules, 200, {"code": 1}, 0, {})
        assert result["passed"] is True

    def test_json_schema_operator_failure(self):
        schema = {"type": "object", "required": ["code"]}
        rules = [{"target": "body", "operator": "json_schema", "expected": schema}]
        result = execute_assertions(rules, 200, {"no_code": 1}, 0, {})
        assert result["passed"] is False
