"""
AutoTest 统一断言引擎

消除 autotest_execution.py 和 autotest_scenario_runner.py 中的重复断言逻辑。
所有断言比较、字段提取、变量提取统一在此模块实现。
"""

import json
import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

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
        header_name = field[len("headers."):]
        return (response_headers or {}).get(header_name)
    else:
        # 从响应 JSON 中提取
        path = field
        for prefix in ("json_body.", "response.", "body."):
            if path.startswith(prefix):
                path = path[len(prefix):]
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


def _validate_json_schema(actual: Any, schema: Any) -> bool:
    """
    使用 jsonschema 校验实际响应是否符合 JSON Schema。
    schema 可以是 dict 或 JSON 字符串。
    """
    if not schema:
        return True

    # 解析字符串 schema
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except (json.JSONDecodeError, TypeError):
            _logger.warning("JSON Schema 解析失败")
            return False

    if not isinstance(schema, dict):
        return False

    try:
        import jsonschema
        jsonschema.validate(instance=actual, schema=schema)
        return True
    except ImportError:
        _logger.warning("jsonschema 未安装，无法执行 JSON Schema 校验")
        return False
    except Exception as e:
        _logger.info(f"JSON Schema 校验失败: {e}")
        return False


def get_operator_text(operator: str) -> str:
    """获取操作符的中文描述"""
    mapping = {
        "equals": "等于", "eq": "等于", "==": "等于",
        "not_equals": "不等于", "ne": "不等于", "!=": "不等于",
        "contains": "包含", "not_contains": "不包含",
        "gt": "大于", ">": "大于",
        "lt": "小于", "<": "小于",
        "gte": "大于等于", ">=": "大于等于",
        "lte": "小于等于", "<=": "小于等于",
        "regex": "正则匹配", "match": "正则匹配",
        "json_exists": "存在", "exists": "存在", "not_exists": "不存在",
        "range": "范围", "empty": "为空", "not_empty": "不为空",
        "json_schema": "JSON Schema 校验",
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
        "eq": "equals", "equal": "equals",
        "ne": "not_equals", "not_equal": "not_equals",
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
            details.append({
                "type": "default_status_code",
                "expected": "2xx/3xx",
                "actual": status_code,
                "passed": False,
            })
        else:
            details.append({
                "type": "default_status_code",
                "expected": "2xx/3xx",
                "actual": status_code,
                "passed": True,
            })
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
            operator = _normalize_operator(rule)
            expected = _normalize_expected(rule)
            actual = get_field_value(field, status_code, response_body, response_time_ms, response_headers)
            passed = compare_values(actual, operator, expected)

            if not passed:
                all_passed = False
                error_messages.append(f"字段 {field} {get_operator_text(operator)} {expected}，实际: {actual}")

            details.append({
                "type": "assertion",
                "field": field,
                "operator": operator,
                "expected": expected,
                "actual": actual,
                "passed": passed,
            })

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
            details.append({
                "type": "status_code",
                "expected": expected,
                "actual": status_code,
                "passed": passed,
            })

        if "json_path" in assert_rules and isinstance(response_body, dict):
            for path, rule in assert_rules["json_path"].items():
                value = extract_jsonpath_value(response_body, path)
                if isinstance(rule, dict):
                    if "eq" in rule:
                        passed = compare_values(value, "equals", rule["eq"])
                        if not passed:
                            all_passed = False
                            error_messages.append(f"JSON路径 {path} 断言失败: 期望 {rule['eq']}, 实际 {value}")
                        details.append({
                            "type": "json_path", "path": path, "assertion": "eq",
                            "expected": rule["eq"], "actual": value, "passed": passed,
                        })
                    elif "contains" in rule:
                        passed = value is not None and rule["contains"] in str(value)
                        if not passed:
                            all_passed = False
                            error_messages.append(f"JSON路径 {path} 不包含: {rule['contains']}")
                        details.append({
                            "type": "json_path", "path": path, "assertion": "contains",
                            "expected": rule["contains"], "actual": value, "passed": passed,
                        })
                else:
                    # 直接比较值（使用 compare_values 统一类型转换）
                    passed = compare_values(value, "equals", rule)
                    if not passed:
                        all_passed = False
                        error_messages.append(f"JSON路径 {path} 断言失败: 期望 {rule}, 实际 {value}")
                    details.append({
                        "type": "json_path", "path": path, "assertion": "eq",
                        "expected": rule, "actual": value, "passed": passed,
                    })

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
        default_value = extractor.get("defaultValue") or extractor.get("default", "")

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
