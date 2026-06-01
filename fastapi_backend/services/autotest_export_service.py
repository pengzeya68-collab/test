"""
AutoTest 导出服务

功能：
- 导出为 OpenAPI 3.0 文档
- 导出为 Python requests 代码
- 导出为 cURL 命令
- 从用例生成 API 文档
"""

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def export_openapi(cases: List[Dict], title: str = "TestMaster API", version: str = "1.0.0") -> Dict:
    """
    将用例列表转为 OpenAPI 3.0 文档。
    """
    paths = {}

    for case in cases:
        url = case.get("url", "")
        method = case.get("method", "GET").lower()
        name = case.get("name", "")
        description = case.get("description", "")

        # 解析 URL 路径
        parsed = urlparse(url)
        path = parsed.path or url
        if not path.startswith("/"):
            path = "/" + path

        # 将路径参数转换为 OpenAPI 格式: {id} -> {id}
        # 已经是正确格式

        if path not in paths:
            paths[path] = {}

        # 构建请求体
        request_body = None
        body_type = case.get("body_type", "none")
        payload = case.get("payload")

        if method in ("post", "put", "patch") and payload:
            content_type = case.get("content_type", "application/json")
            if body_type == "form-data":
                content_type = "application/x-www-form-urlencoded"
            elif body_type == "multipart":
                content_type = "multipart/form-data"
            elif body_type in ("xml", "raw_xml"):
                content_type = "application/xml"

            request_body = {
                "content": {
                    content_type: {
                        "schema": _json_to_schema(payload)
                    }
                }
            }

        # 构建参数
        parameters = []
        params = case.get("params")
        if params and isinstance(params, dict):
            for k, v in params.items():
                parameters.append({
                    "name": k,
                    "in": "query",
                    "schema": {"type": _guess_type(v)},
                    "example": v,
                })

        # 构建 headers
        headers = case.get("headers")
        if headers and isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() not in ("content-type", "authorization"):
                    parameters.append({
                        "name": k,
                        "in": "header",
                        "schema": {"type": "string"},
                        "example": v,
                    })

        operation = {
            "summary": name,
            "description": description,
            "operationId": f"{method}_{path.replace('/', '_').strip('_')}",
            "tags": [case.get("group_name", "default")],
            "responses": {
                "200": {
                    "description": "成功",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            }
        }

        if parameters:
            operation["parameters"] = parameters
        if request_body:
            operation["requestBody"] = request_body

        paths[path][method] = operation

    return {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": "由 TestMaster 自动生成的 API 文档",
        },
        "paths": paths,
    }


def export_python_code(cases: List[Dict]) -> str:
    """将用例列表导出为 Python requests 代码"""
    lines = [
        '"""',
        '由 TestMaster 自动生成的 API 测试代码',
        '"""',
        'import requests',
        'import json',
        '',
        '',
    ]

    for i, case in enumerate(cases):
        method = case.get("method", "GET").upper()
        url = case.get("url", "")
        headers = case.get("headers", {})
        payload = case.get("payload")
        body_type = case.get("body_type", "none")
        name = case.get("name", f"test_case_{i+1}")

        # 函数名
        func_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower()).strip('_')
        if not func_name:
            func_name = f"test_case_{i+1}"

        lines.append(f'def {func_name}():')
        lines.append(f'    """{name}"""')
        lines.append(f'    url = "{url}"')

        if headers:
            lines.append(f'    headers = {json.dumps(headers, ensure_ascii=False)}')
        else:
            lines.append(f'    headers = {{}}')

        if payload and method in ("POST", "PUT", "PATCH"):
            if body_type == "form-data":
                lines.append(f'    data = {json.dumps(payload, ensure_ascii=False)}')
                lines.append(f'    response = requests.{method.lower()}(url, headers=headers, data=data)')
            elif body_type == "graphql":
                graphql_body = {"query": payload.get("query", "") if isinstance(payload, dict) else str(payload)}
                if isinstance(payload, dict) and "variables" in payload:
                    graphql_body["variables"] = payload["variables"]
                lines.append(f'    payload = {json.dumps(graphql_body, ensure_ascii=False)}')
                lines.append(f'    response = requests.{method.lower()}(url, headers=headers, json=payload)')
            else:
                lines.append(f'    payload = {json.dumps(payload, ensure_ascii=False)}')
                lines.append(f'    response = requests.{method.lower()}(url, headers=headers, json=payload)')
        else:
            lines.append(f'    response = requests.{method.lower()}(url, headers=headers)')

        lines.append(f'    print(f"Status: {{response.status_code}}")')
        lines.append(f'    print(f"Body: {{response.text[:500]}}")')
        lines.append(f'    return response')
        lines.append('')
        lines.append('')

    return '\n'.join(lines)


def export_curl(cases: List[Dict]) -> List[str]:
    """将用例列表导出为 cURL 命令"""
    curls = []

    for case in cases:
        method = case.get("method", "GET").upper()
        url = case.get("url", "")
        headers = case.get("headers", {})
        payload = case.get("payload")
        body_type = case.get("body_type", "none")

        parts = [f'curl -X {method} "{url}"']

        for k, v in headers.items():
            parts.append(f'  -H "{k}: {v}"')

        if payload and method in ("POST", "PUT", "PATCH"):
            if body_type == "form-data" and isinstance(payload, dict):
                for k, v in payload.items():
                    parts.append(f'  -d "{k}={v}"')
            else:
                body_str = json.dumps(payload, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
                parts.append(f"  --data-raw '{body_str}'")

        curls.append(" \\\n".join(parts))

    return curls


def _json_to_schema(value: Any) -> Dict:
    """将 JSON 值转换为 OpenAPI Schema"""
    if isinstance(value, dict):
        properties = {}
        for k, v in value.items():
            properties[k] = _json_to_schema(v)
        return {"type": "object", "properties": properties}
    elif isinstance(value, list):
        if value:
            return {"type": "array", "items": _json_to_schema(value[0])}
        return {"type": "array", "items": {}}
    elif isinstance(value, bool):
        return {"type": "boolean", "example": value}
    elif isinstance(value, int):
        return {"type": "integer", "example": value}
    elif isinstance(value, float):
        return {"type": "number", "example": value}
    else:
        return {"type": "string", "example": str(value)}


def _guess_type(value: Any) -> str:
    """猜测值的 OpenAPI 类型"""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    return "string"
