"""
变量解析引擎
按照用户 Prompt 2 要求实现

功能：
- 查找字符串中的 {{variable_name}} 占位符
- 使用 variables 字典中的值替换占位符
- 递归处理 JSON 字典
"""
import re
from typing import Any, Dict, List, Union, Text


def find_variables(text: str) -> List[str]:
    """
    查找字符串中所有的 {{variable_name}} 占位符

    Args:
        text: 包含占位符的字符串

    Returns:
        找到的变量名列表（去重）

    Example:
        >>> find_variables("{{base_url}}{{api_prefix}}/login")
        ['base_url', 'api_prefix']
    """
    if not isinstance(text, str):
        return []

    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, text)
    return list(set(matches))


def replace_variables_in_text(text: str, variables: Dict[str, Any]) -> str:
    """
    替换字符串中的 {{variable}} 占位符

    Args:
        text: 包含占位符的字符串
        variables: 变量字典 {variable_name: value}

    Returns:
        替换后的字符串

    Example:
        >>> replace_variables_in_text("{{base_url}}{{api_prefix}}/login", {"base_url": "https://api.com", "api_prefix": "/v1"})
        'https://api.com/v1/login'
    """
    if not isinstance(text, str):
        return text

    def replace_match(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))

    # 替换所有 {{variable}} 格式的占位符
    pattern = r'\{\{(\w+)\}\}'
    return re.sub(pattern, replace_match, text)


def replace_variables(obj: Any, variables: Dict[str, Any]) -> Any:
    """
    递归替换对象中的所有 {{variable}} 占位符

    支持：
    - 字符串：直接替换
    - 字典：递归处理每个值
    - 列表：递归处理每个元素
    - 其他类型：直接返回

    Args:
        obj: 要处理的对象（字符串、字典、列表等）
        variables: 变量字典

    Returns:
        替换后的对象

    Example:
        >>> data = {
        ...     "url": "{{base_url}}{{api_prefix}}/login",
        ...     "headers": {"Authorization": "Bearer {{token}}"},
        ...     "body": {"username": "{{username}}"}
        ... }
        >>> replace_variables(data, {"base_url": "https://api.com", "api_prefix": "/v1", "token": "abc123", "username": "admin"})
        {
            "url": "https://api.com/v1/login",
            "headers": {"Authorization": "Bearer abc123"},
            "body": {"username": "admin"}
        }
    """
    if isinstance(obj, str):
        return replace_variables_in_text(obj, variables)
    elif isinstance(obj, dict):
        return {key: replace_variables(value, variables) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [replace_variables(item, variables) for item in obj]
    else:
        return obj


def validate_variables(text: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证字符串中的占位符是否都有对应的变量值

    Args:
        text: 包含占位符的字符串
        variables: 变量字典

    Returns:
        {
            "valid": bool,  # 是否所有占位符都有对应的值
            "missing": List[str],  # 缺失的变量名列表
            "found": List[str]  # 找到的变量名列表
        }

    Example:
        >>> validate_variables("{{base_url}}{{api_prefix}}/login", {"base_url": "https://api.com"})
        {
            "valid": False,
            "missing": ["api_prefix"],
            "found": ["base_url", "api_prefix"]
        }
    """
    found = find_variables(text)
    missing = [var for var in found if var not in variables]

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "found": found
    }


# ========== 单元测试 ==========

if __name__ == "__main__":
    # 测试 find_variables
    assert find_variables("{{base_url}}{{api_prefix}}/login") == ["base_url", "api_prefix"]
    assert find_variables("no variables here") == []
    assert find_variables("{{name}} and {{name}}") == ["name"]
    print("✓ find_variables 测试通过")

    # 测试 replace_variables_in_text
    variables = {
        "base_url": "https://api.example.com",
        "api_prefix": "/v1",
        "token": "abc123"
    }
    result = replace_variables_in_text("{{base_url}}{{api_prefix}}/login", variables)
    assert result == "https://api.example.com/v1/login"
    print("✓ replace_variables_in_text 测试通过")

    # 测试递归替换
    data = {
        "url": "{{base_url}}{{api_prefix}}/login",
        "headers": {
            "Authorization": "Bearer {{token}}",
            "Content-Type": "application/json"
        },
        "body": {
            "username": "admin",
            "password": "{{password}}"
        },
        "list": ["{{base_url}}", "{{token}}"]
    }

    full_variables = {
        "base_url": "https://api.example.com",
        "api_prefix": "/v1",
        "token": "abc123",
        "password": "secret"
    }

    replaced = replace_variables(data, full_variables)
    assert replaced["url"] == "https://api.example.com/v1/login"
    assert replaced["headers"]["Authorization"] == "Bearer abc123"
    assert replaced["body"]["password"] == "secret"
    assert replaced["list"][0] == "https://api.example.com"
    print("✓ replace_variables 递归替换 测试通过")

    # 测试 validate_variables
    validation = validate_variables("{{base_url}}{{api_prefix}}/login", {"base_url": "https://api.com"})
    assert validation["valid"] == False
    assert "api_prefix" in validation["missing"]
    print("✓ validate_variables 测试通过")

    print("\n所有测试通过！✓")
