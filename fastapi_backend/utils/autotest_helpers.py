"""
AutoTest 纯工具函数
仅包含无副作用的 JSON 处理和 JSONPath 提取函数
有副作用的函数已迁移:
- save_variables_to_db → services/autotest_variable_service.py
- write_allure_results → services/autotest_report_service.py
"""

import json
import logging
from typing import Any

_logger = logging.getLogger(__name__)


def convert_to_dict(data) -> dict:
    if data is None or data == "":
        return {}
    elif isinstance(data, str):
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return parsed
            return {}
        except json.JSONDecodeError:
            _logger.warning(f"JSON解析失败，数据将被丢弃: {str(data)[:100]}")
            return {}
    elif isinstance(data, dict):
        return data
    elif isinstance(data, list):
        # list 格式 headers: [{"name": "X-Auth", "value": "token"}]
        result = {}
        for item in data:
            if isinstance(item, dict) and "name" in item:
                result[str(item["name"])] = str(item.get("value", ""))
        return result
    return {}


def extract_jsonpath_value(data: Any, path: str, default: Any = None) -> Any:
    """
    从 JSON 数据中提取值，支持完整 JSONPath 语法。
    优先使用 jsonpath-ng 库，失败时回退到内置简化解析器。
    支持: $.data.id, $.items[0].name, $.items[*].id, data.id, items[0].name
    """
    if not path:
        return default

    # 优先使用 jsonpath-ng
    try:
        from jsonpath_ng.ext import parse as jp_parse

        # 标准化路径：确保以 $ 开头
        normalized = path if path.startswith("$") else f"$.{path}"
        matches = jp_parse(normalized).find(data)
        if matches:
            # 单个匹配返回值，多个匹配返回列表
            values = [m.value for m in matches]
            return values[0] if len(values) == 1 else values
        return default
    except Exception:
        # jsonpath-ng 解析失败，回退到内置解析器
        pass

    # 内置简化解析器（向后兼容）
    path = path.replace("$.", "").replace("$", "")

    keys = []
    current = ""
    i = 0
    while i < len(path):
        char = path[i]
        if char == ".":
            if current:
                keys.append(current)
                current = ""
        elif char == "[":
            if current:
                keys.append(current)
                current = ""
            j = i + 1
            while j < len(path) and path[j] != "]":
                j += 1
            index_str = path[i + 1 : j]
            if index_str == "*":
                keys.append("*")
            else:
                try:
                    keys.append(int(index_str))
                except ValueError:
                    keys.append(index_str)
            i = j
        elif char == "]":
            pass
        else:
            current += char
        i += 1

    if current:
        keys.append(current)

    value = data
    for key in keys:
        if key == "*":
            # 通配符：展开列表
            if isinstance(value, list):
                # 如果是最后一个 key，返回整个列表
                return value
            # 如果后面还有 key，对每个元素递归提取
            return default
        elif isinstance(key, int):
            if isinstance(value, list) and 0 <= key < len(value):
                value = value[key]
            else:
                return default
        elif isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default

    return value
