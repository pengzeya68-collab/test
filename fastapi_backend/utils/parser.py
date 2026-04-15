"""
变量解析工具
支持 {{variable_name}} 格式的占位符查找和替换
"""
import re
import time
import random
import uuid
from typing import Any, Dict, List


def find_variables(text: str) -> List[str]:
    """查找字符串中所有的 {{variable_name}} 占位符"""
    if not isinstance(text, str):
        return []
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, text)
    return list(set(matches))


def replace_variables_in_text(text: str, variables: Dict[str, Any]) -> str:
    """替换字符串中的 {{variable}} 占位符"""
    if not isinstance(text, str):
        return text

    def replace_match(match):
        var_name = match.group(1)
        
        if var_name.startswith('$'):
            if var_name == '$timestamp':
                return str(int(time.time()))
            elif var_name == '$random_int':
                return str(random.randint(1, 10000))
            elif var_name == '$random_string':
                import string
                letters = string.ascii_letters + string.digits
                return ''.join(random.choice(letters) for _ in range(10))
            elif var_name == '$uuid':
                return str(uuid.uuid4())
            elif var_name == '$datetime':
                return time.strftime('%Y-%m-%d %H:%M:%S')
        
        if var_name in variables:
            return str(variables[var_name])
        return match.group(0)

    pattern = r'\{\{(\w+)\}\}'
    return re.sub(pattern, replace_match, text)


def replace_variables(obj: Any, variables: Dict[str, Any]) -> Any:
    """递归替换对象中的所有 {{variable}} 占位符"""
    if isinstance(obj, str):
        return replace_variables_in_text(obj, variables)
    elif isinstance(obj, dict):
        return {key: replace_variables(value, variables) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [replace_variables(item, variables) for item in obj]
    else:
        return obj
