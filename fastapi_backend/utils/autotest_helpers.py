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
            return json.loads(data)
        except json.JSONDecodeError:
            _logger.warning(f"JSON解析失败，数据将被丢弃: {str(data)[:100]}")
            return {}
    elif isinstance(data, dict):
        return data
    else:
        return {}


def extract_jsonpath_value(data: Any, path: str, default: Any = None) -> Any:
    """
    从 JSON 数据中提取值（简化版 JSONPath）
    支持: $.data.id, $.items[0].name, data.id, items[0].name, $.items[*].name
    """
    if not path:
        return default

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
            try:
                keys.append(int(index_str))
            except ValueError:
                # 支持 [*] 通配符语法
                if index_str == "*":
                    keys.append("*")
            i = j
        elif char == "]":
            pass
        else:
            current += char
        i += 1

    if current:
        keys.append(current)

    def _apply(value, remaining_keys):
        """递归应用路径键，支持通配符"""
        for idx, key in enumerate(remaining_keys):
            if key == "*":
                # 通配符：对 list/dict 的所有元素应用剩余路径
                rest = remaining_keys[idx + 1:]
                if isinstance(value, list):
                    return [_apply(item, rest) for item in value]
                elif isinstance(value, dict):
                    return [_apply(item, rest) for item in value.values()]
                else:
                    return default
            elif isinstance(key, int):
                if isinstance(value, list) and 0 <= key < len(value):
                    value = value[key]
                else:
                    return default
            elif isinstance(value, dict):
                if key not in value:
                    return default
                value = value[key]
            else:
                return default
        return value

    return _apply(data, keys)
