"""
AutoTest 统一断言引擎

消除 autotest_execution.py 和 autotest_scenario_runner.py 中的重复断言逻辑。
所有断言比较、字段提取、变量提取统一在此模块实现。
"""

import json
import logging
import math
import re
from typing import Any, Dict, Optional, Tuple

from fastapi_backend.utils.autotest_helpers import extract_jsonpath_value

_logger = logging.getLogger(__name__)


# ========== 字段值提取 ==========


def get_field_value(
    field: str,
    status_code: int,
    response_body: Any,
    response_time_ms: float = 0,
    response_headers: Optional[Dict] = None,
) -> Any:
    """
    统一的字段值提取。
    支持: status_code, response_time, headers.xxx, body.xxx (JSONPath), 纯 JSONPath

    Args:
        field: 字段名
        status_code: HTTP 状态码
        response_body: 响应体（已解析的 dict/list 或原始文本）
        response_time_ms: 响应时间(毫秒)
        response_headers: 响应头字典
    """
    if field == "status_code":
        return status_code
    elif field == "response_time":
        return response_time_ms
    elif field in ("body", "response_body", "json_body"):
        return response_body
    elif field == "headers":
        return response_headers or {}
    elif field.startswith("headers."):
        header_name = field[len("headers.") :]
        return (response_headers or {}).get(header_name)
    else:
        # 从响应 JSON 中提取
        path = field
        for prefix in ("json_body.", "response.", "body."):
            if path.startswith(prefix):
                path = path[len(prefix) :]
                break

        if isinstance(response_body, dict):
            return extract_jsonpath_value(response_body, path)
        elif isinstance(response_body, list):
            return extract_jsonpath_value(response_body, path)
        return None


# ========== 比较函数 ==========


def compare_values(actual: Any, operator: str, expected: Any) -> bool:
    """
    统一的值比较函数。正确处理 None 值。
    支持所有操作符: equals, not_equals, contains, not_contains, gt, lt, gte, lte,
    regex, json_exists, range, exists, not_exists, empty, not_empty
    """
    # None 值特殊处理
    if actual is None:
        if operator in ("json_exists", "exists"):
            return False
        if operator in ("not_exists",):
            return True
        if operator in ("not_equals", "ne", "!="):
            return expected is not None
        if operator in ("empty",):
            return True
        if operator in ("not_empty",):
            return False
        # 其他操作符对 None 值返回 False
        return False

    if operator in ("equals", "eq", "=="):
        # 优先数值比较，无法转数值时回退到字符串比较
        try:
            return math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9)
        except (ValueError, TypeError):
            return str(actual) == str(expected)
    elif operator in ("not_equals", "ne", "!="):
        # 使用与 equals 完全相反的逻辑，确保一致性
        try:
            return not math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9)
        except (ValueError, TypeError):
            return str(actual) != str(expected)
    elif operator == "contains":
        return str(expected) in str(actual)
    elif operator == "not_contains":
        return str(expected) not in str(actual)
    elif operator in ("gt", ">"):
        try:
            return float(actual) > float(expected)
        except (ValueError, TypeError):
            return False
    elif operator in ("lt", "<"):
        try:
            return float(actual) < float(expected)
        except (ValueError, TypeError):
            return False
    elif operator in ("gte", ">="):
        try:
            return float(actual) >= float(expected)
        except (ValueError, TypeError):
            return False
    elif operator in ("lte", "<="):
        try:
            return float(actual) <= float(expected)
        except (ValueError, TypeError):
            return False
    elif operator in ("regex", "match"):
        try:
            return bool(re.search(str(expected), str(actual)))
        except Exception:
            return False
    elif operator in ("json_exists", "exists"):
        return actual is not None
    elif operator == "not_exists":
        return actual is None
    elif operator == "empty":
        return not actual
    elif operator == "not_empty":
        return bool(actual)
    elif operator == "range":
        return _check_range(actual, expected)
    elif operator == "json_schema":
        return _validate_json_schema(actual, expected)
    _logger.warning(f"未知的断言操作符: {operator}")
    return False


def _check_range(actual: Any, expected: Any) -> bool:
    """检查值是否在指定范围内（如 2xx, 3xx, 4xx, 5xx）"""
    try:
        val = int(actual)
    except (ValueError, TypeError):
        return False

    range_text = str(expected).lower()
    if "2xx/3xx" in range_text or ("2xx" in range_text and "3xx" in range_text):
        return 200 <= val < 400
    elif "2xx" == range_text:
        return 200 <= val < 300
    elif "3xx" == range_text:
        return 300 <= val < 400
    elif "4xx" == range_text:
        return 400 <= val < 500
    elif "5xx" == range_text:
        return 500 <= val < 600
    # 无法识别的范围格式，返回 False 而非默默 fallback
    _logger.warning(f"无法识别的范围断言格式: {expected}")
    return False


def _format_schema_path(path: Any) -> str:
    """
    将 jsonschema 错误的 absolute_path 格式化为可读字符串。
    示例: ['data', 'id'] -> "data.id"; ['items', 0, 'name'] -> "items[0].name"
    空路径（根级错误）返回 "(根)"。
    """
    if not path:
        return "(根)"
    parts = []
    for p in path:
        if isinstance(p, int):
            parts.append(f"[{p}]")
        else:
            parts.append(("." if parts else "") + str(p))
    return "".join(parts) if parts else "(根)"


def _validate_json_schema_detailed(actual: Any, schema: Any) -> Tuple[bool, Optional[str]]:
    """
    使用 jsonschema 校验实例是否符合 JSON Schema，返回详细错误信息。

    Args:
        actual: 待校验实例（dict/list/标量，需为 JSON 可校验类型）
        schema: JSON Schema（dict 或 JSON 字符串）

    Returns:
        (passed, error_message): passed 为 True 时 error_message 为 None；
        passed 为 False 时 error_message 形如
        "Schema 验证失败: <字段路径> - <错误原因>" 或 "Schema 格式错误: ..."。
    """
    # 空 schema 视为通过
    if not schema:
        return True, None

    # 解析字符串 schema
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except (json.JSONDecodeError, TypeError):
            return False, "Schema 验证失败: (根) - schema 不是合法的 JSON 字符串"

    if not isinstance(schema, dict):
        return False, f"Schema 验证失败: (根) - schema 必须为对象, 实际为 {type(schema).__name__}"

    try:
        import jsonschema
    except ImportError:
        return False, "jsonschema 库未安装，无法执行 JSON Schema 校验"

    try:
        # 先校验 schema 本身是否合法（非法时抛出 SchemaError）
        jsonschema.Draft7Validator.check_schema(schema)
        validator = jsonschema.Draft7Validator(schema)
        # 排序：取最靠近根的错误，便于定位；将路径转为字符串避免 str/int 比较异常
        errors = sorted(validator.iter_errors(actual), key=lambda e: list(map(str, e.absolute_path)))
    except jsonschema.SchemaError as e:
        path = _format_schema_path(getattr(e, "absolute_path", []))
        return False, f"Schema 格式错误: {path} - {e.message}"
    except Exception as e:
        return False, f"Schema 校验异常: {str(e)}"

    if not errors:
        return True, None

    first_err = errors[0]
    path = _format_schema_path(first_err.absolute_path)
    return False, f"Schema 验证失败: {path} - {first_err.message}"


def _validate_json_schema(actual: Any, schema: Any) -> bool:
    """
    使用 jsonschema 校验实际响应是否符合 JSON Schema（返回布尔值）。
    供 json_schema 操作符使用；详细错误信息见 _validate_json_schema_detailed。
    """
    passed, _ = _validate_json_schema_detailed(actual, schema)
    return passed


def _handle_json_schema_target(rule: Dict, response_body: Any) -> Dict[str, Any]:
    """
    处理 json_schema target 类型的断言。

    - 操作符: matches（符合 schema）、not_matches（不符合 schema）
    - schema 从 expected_schema 字段读取，兼容 expected/expectedValue
    - 响应体为字符串时尝试解析为 JSON；解析失败按“非 JSON”处理
    - 错误信息包含具体的 schema 验证失败路径

    Returns:
        {"passed": bool, "message": Optional[str], "detail": dict}
    """
    operator = _normalize_operator(rule)
    schema = rule.get("expected_schema")
    if schema is None:
        schema = _normalize_expected(rule)

    # not_matches 语义：符合则失败，不符合则通过
    is_not_match = operator in ("not_matches", "not_match")

    # 响应体预处理：字符串尝试解析为 JSON，便于校验 JSON 字符串响应
    instance = response_body
    non_json = False
    if isinstance(response_body, str):
        try:
            instance = json.loads(response_body)
        except (json.JSONDecodeError, ValueError):
            non_json = True

    # 响应体非 JSON 格式时的处理
    if non_json:
        if is_not_match:
            passed = True
            message = "响应体非 JSON 格式，符合 not_matches 语义"
        else:
            passed = False
            message = "Schema 验证失败: (根) - 响应体非 JSON 格式，无法执行 Schema 校验"
    else:
        ok, err = _validate_json_schema_detailed(instance, schema)
        if is_not_match:
            passed = not ok
            # not_matches 通过时不输出错误信息
            message = None if passed else (err or "Schema 验证通过，与 not_matches 语义不符")
        else:
            passed = ok
            message = err

    return {
        "passed": passed,
        "message": message,
        "detail": {
            "type": "json_schema",
            "field": "json_schema",
            "operator": operator,
            "expected": schema,
            "actual": response_body,
            "passed": passed,
            "message": message,
        },
    }


def get_operator_text(operator: str) -> str:
    """获取操作符的中文描述"""
    mapping = {
        "equals": "等于",
        "eq": "等于",
        "==": "等于",
        "not_equals": "不等于",
        "ne": "不等于",
        "!=": "不等于",
        "contains": "包含",
        "not_contains": "不包含",
        "gt": "大于",
        ">": "大于",
        "lt": "小于",
        "<": "小于",
        "gte": "大于等于",
        ">=": "大于等于",
        "lte": "小于等于",
        "<=": "小于等于",
        "regex": "正则匹配",
        "match": "正则匹配",
        "json_exists": "存在",
        "exists": "存在",
        "not_exists": "不存在",
        "range": "范围",
        "empty": "为空",
        "not_empty": "不为空",
        "json_schema": "JSON Schema 校验",
        "matches": "符合 Schema",
        "not_matches": "不符合 Schema",
    }
    return mapping.get(operator, operator)


# ========== 断言规则标准化 ==========


def _normalize_expected(rule: Dict) -> Any:
    """从断言规则中提取 expected 值，兼容多种 key 命名"""
    expected = rule.get("expectedValue")
    if expected is not None:
        return expected
    expected = rule.get("expected")
    if expected is not None:
        return expected
    expected = rule.get("value")
    if expected is not None:
        return expected
    expected = rule.get("eq")
    if expected is not None:
        return expected
    return ""


def _normalize_operator(rule: Dict) -> str:
    """从断言规则中提取操作符，兼容多种 key 命名"""
    op = rule.get("operator") or rule.get("condition") or "equals"
    op_map = {
        "eq": "equals",
        "equal": "equals",
        "ne": "not_equals",
        "not_equal": "not_equals",
        "match": "regex",
    }
    return op_map.get(op, op)


def _normalize_field(rule: Dict) -> str:
    """从断言规则中提取字段名"""
    return rule.get("field") or rule.get("target", "")


# ========== 断言执行 ==========


def execute_assertions(
    assert_rules: Any,
    status_code: int,
    response_body: Any,
    response_time_ms: float = 0,
    response_headers: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    统一的断言执行入口。
    支持数组格式和对象格式的断言规则。

    Returns:
        {"passed": bool, "message": str, "details": list, "has_status_code_assertion": bool}
    """
    details = []
    all_passed = True
    error_messages = []
    has_status_code_assertion = False

    if not assert_rules:
        # 无断言规则时，仅做默认状态码检查
        if not (200 <= status_code < 400):
            all_passed = False
            error_messages.append(f"默认断言失败: 期望 2xx/3xx, 实际返回 {status_code}")
            details.append(
                {
                    "type": "default_status_code",
                    "expected": "2xx/3xx",
                    "actual": status_code,
                    "passed": False,
                }
            )
        else:
            details.append(
                {
                    "type": "default_status_code",
                    "expected": "2xx/3xx",
                    "actual": status_code,
                    "passed": True,
                }
            )
        return {
            "passed": all_passed,
            "message": "; ".join(error_messages) if error_messages else "默认状态码检查通过",
            "details": details,
            "has_status_code_assertion": False,
        }

    # 数组格式
    if isinstance(assert_rules, list):
        for rule in assert_rules:
            if not isinstance(rule, dict):
                continue
            field = _normalize_field(rule)
            if field == "status_code":
                has_status_code_assertion = True

            # JSON Schema target 类型特殊处理：对整个响应体做 Schema 校验
            if field == "json_schema":
                schema_result = _handle_json_schema_target(rule, response_body)
                if not schema_result["passed"]:
                    all_passed = False
                    error_messages.append(schema_result["message"] or "JSON Schema 断言失败")
                details.append(schema_result["detail"])
                continue

            operator = _normalize_operator(rule)
            expected = _normalize_expected(rule)
            expression = rule.get("expression")
            effective_field = expression if expression and field in {"body", "response_body", "json_body"} else field
            actual = get_field_value(effective_field, status_code, response_body, response_time_ms, response_headers)
            passed = compare_values(actual, operator, expected)

            if not passed:
                all_passed = False
                error_messages.append(f"字段 {field} {get_operator_text(operator)} {expected}，实际: {actual}")

            details.append(
                {
                    "type": "assertion",
                    "field": effective_field,
                    "operator": operator,
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                }
            )

    # 对象格式
    elif isinstance(assert_rules, dict):
        if "status_code" in assert_rules:
            has_status_code_assertion = True
            expected = assert_rules["status_code"]
            if isinstance(expected, dict):
                operator = expected.get("operator", "equals")
                expected_value = _normalize_expected(expected)
                if operator == "range":
                    passed = compare_values(status_code, "range", expected_value)
                else:
                    passed = compare_values(status_code, operator, expected_value)
            else:
                passed = status_code == expected

            if not passed:
                all_passed = False
                error_messages.append(f"状态码断言失败: 期望 {expected}, 实际 {status_code}")
            details.append(
                {
                    "type": "status_code",
                    "expected": expected,
                    "actual": status_code,
                    "passed": passed,
                }
            )

        if "json_path" in assert_rules and isinstance(response_body, (dict, list)):
            for path, rule in assert_rules["json_path"].items():
                value = extract_jsonpath_value(response_body, path)
                if isinstance(rule, dict):
                    if "eq" in rule:
                        passed = compare_values(value, "equals", rule["eq"])
                        if not passed:
                            all_passed = False
                            error_messages.append(f"JSON路径 {path} 断言失败: 期望 {rule['eq']}, 实际 {value}")
                        details.append(
                            {
                                "type": "json_path",
                                "path": path,
                                "assertion": "eq",
                                "expected": rule["eq"],
                                "actual": value,
                                "passed": passed,
                            }
                        )
                    elif "contains" in rule:
                        passed = value is not None and rule["contains"] in str(value)
                        if not passed:
                            all_passed = False
                            error_messages.append(f"JSON路径 {path} 不包含: {rule['contains']}")
                        details.append(
                            {
                                "type": "json_path",
                                "path": path,
                                "assertion": "contains",
                                "expected": rule["contains"],
                                "actual": value,
                                "passed": passed,
                            }
                        )
                else:
                    # 直接比较值（使用 compare_values 统一类型转换）
                    passed = compare_values(value, "equals", rule)
                    if not passed:
                        all_passed = False
                        error_messages.append(f"JSON路径 {path} 断言失败: 期望 {rule}, 实际 {value}")
                    details.append(
                        {
                            "type": "json_path",
                            "path": path,
                            "assertion": "eq",
                            "expected": rule,
                            "actual": value,
                            "passed": passed,
                        }
                    )

        # 响应头断言（对象格式）：支持 eq / contains，或直接比较
        if "response_header" in assert_rules:
            header_rules = assert_rules["response_header"]
            if isinstance(header_rules, dict):
                for header_name, rule in header_rules.items():
                    actual_value = (response_headers or {}).get(header_name)
                    if isinstance(rule, dict):
                        if "eq" in rule:
                            passed = compare_values(actual_value, "equals", rule["eq"])
                            if not passed:
                                all_passed = False
                                error_messages.append(
                                    f"响应头 {header_name} 断言失败: 期望 {rule['eq']}, 实际 {actual_value}"
                                )
                        elif "contains" in rule:
                            passed = actual_value is not None and rule["contains"] in str(actual_value)
                            if not passed:
                                all_passed = False
                                error_messages.append(f"响应头 {header_name} 不包含: {rule['contains']}")
                        else:
                            operator = rule.get("operator", "equals")
                            expected_value = _normalize_expected(rule)
                            passed = compare_values(actual_value, operator, expected_value)
                            if not passed:
                                all_passed = False
                                error_messages.append(
                                    f"响应头 {header_name} 断言失败: 期望 {expected_value}, 实际 {actual_value}"
                                )
                    else:
                        passed = compare_values(actual_value, "equals", rule)
                        if not passed:
                            all_passed = False
                            error_messages.append(f"响应头 {header_name} 断言失败: 期望 {rule}, 实际 {actual_value}")
                    details.append(
                        {
                            "type": "response_header",
                            "header_name": header_name,
                            "expected": rule,
                            "actual": actual_value,
                            "passed": passed,
                        }
                    )

        # 响应时间断言（对象格式）：支持 lt / lte / gt / gte / eq / range
        if "response_time" in assert_rules:
            rule = assert_rules["response_time"]
            if isinstance(rule, dict):
                if "lt" in rule:
                    passed = compare_values(response_time_ms, "lt", rule["lt"])
                    op_text, expected_value = "小于", rule["lt"]
                elif "lte" in rule:
                    passed = compare_values(response_time_ms, "lte", rule["lte"])
                    op_text, expected_value = "小于等于", rule["lte"]
                elif "gt" in rule:
                    passed = compare_values(response_time_ms, "gt", rule["gt"])
                    op_text, expected_value = "大于", rule["gt"]
                elif "gte" in rule:
                    passed = compare_values(response_time_ms, "gte", rule["gte"])
                    op_text, expected_value = "大于等于", rule["gte"]
                elif "eq" in rule:
                    passed = compare_values(response_time_ms, "equals", rule["eq"])
                    op_text, expected_value = "等于", rule["eq"]
                elif "range" in rule:
                    passed = compare_values(response_time_ms, "range", rule["range"])
                    op_text, expected_value = "范围", rule["range"]
                else:
                    operator = rule.get("operator", "equals")
                    expected_value = _normalize_expected(rule)
                    passed = compare_values(response_time_ms, operator, expected_value)
                    op_text = get_operator_text(operator)
            else:
                # 直接给定阈值时按“小于等于”处理
                passed = compare_values(response_time_ms, "lte", rule)
                op_text, expected_value = "小于等于", rule

            if not passed:
                all_passed = False
                error_messages.append(f"响应时间断言失败: 期望 {op_text} {expected_value}ms, 实际 {response_time_ms}ms")
            details.append(
                {
                    "type": "response_time",
                    "operator": op_text,
                    "expected": expected_value,
                    "actual": response_time_ms,
                    "passed": passed,
                }
            )

    # 注意：无断言规则的情况已在上方提前返回（默认 2xx/3xx 检查）
    # 这里不再追加默认 status_code 兜底断言
    # 原因：用户可能有意只断言 $.code/$.detail 等业务字段（如鉴权用例期望 401），
    # 强制 2xx/3xx 兜底会导致这类用例误判失败

    return {
        "passed": all_passed,
        "message": "; ".join(error_messages) if error_messages else "所有断言通过",
        "details": details,
        "has_status_code_assertion": has_status_code_assertion,
    }


# ========== 变量提取 ==========


def extract_variables_from_response(
    extractors: Any,
    response_body: Any,
    response_text: str = "",
    response_headers: Optional[Dict] = None,
) -> Dict[str, str]:
    """
    统一的变量提取。支持 jsonpath, regex, header 三种提取器。
    兼容 camelCase 和 snake_case key 命名。
    """
    if not extractors:
        return {}

    extracted = {}

    for extractor in extractors:
        if not isinstance(extractor, dict):
            continue

        var_name = extractor.get("variableName") or extractor.get("var_name")
        extractor_type = extractor.get("extractorType") or extractor.get("type", "jsonpath")
        expression = extractor.get("expression") or extractor.get("path", "")
        # 注意：不能用 or，否则 0/False 会被当作空值处理
        default_value = extractor.get("defaultValue")
        if default_value is None:
            default_value = extractor.get("default", "")

        # header 提取器用 name 字段而非 expression
        if extractor_type == "header":
            if not var_name or not extractor.get("name"):
                continue
        else:
            if not var_name or not expression:
                continue

        value = default_value

        try:
            if extractor_type == "jsonpath":
                value = extract_jsonpath_value(response_body, expression, default_value)
            elif extractor_type == "regex":
                match = re.search(expression, response_text or str(response_body or ""))
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
            elif extractor_type == "header":
                header_name = (extractor.get("name") or "").lower()
                for h_key, h_val in (response_headers or {}).items():
                    if h_key.lower() == header_name:
                        value = str(h_val)
                        break
        except Exception as e:
            _logger.info(f"变量提取失败 {var_name}: {str(e)}")
            value = default_value

        extracted[var_name] = value

    return extracted
