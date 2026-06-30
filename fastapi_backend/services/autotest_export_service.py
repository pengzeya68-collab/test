"""
AutoTest 导出服务

功能：
- 导出为 OpenAPI 3.0 文档
- 导出为 Python requests 代码
- 导出为 cURL 命令
- 从用例生成 API 文档
- 文档即用例 - 自动聚合执行历史、Mock、场景等数据
"""

import fnmatch
import json
import re
from datetime import datetime, timezone
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

            request_body = {"content": {content_type: {"schema": _json_to_schema(payload)}}}

        # 构建参数
        parameters = []
        params = case.get("params")
        if params and isinstance(params, dict):
            for k, v in params.items():
                parameters.append(
                    {
                        "name": k,
                        "in": "query",
                        "schema": {"type": _guess_type(v)},
                        "example": v,
                    }
                )

        # 构建 headers
        headers = case.get("headers")
        if headers and isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() not in ("content-type", "authorization"):
                    parameters.append(
                        {
                            "name": k,
                            "in": "header",
                            "schema": {"type": "string"},
                            "example": v,
                        }
                    )

        operation = {
            "summary": name,
            "description": description,
            "operationId": f"{method}_{path.replace('/', '_').strip('_')}",
            "tags": [case.get("group_name", "default")],
            "responses": {
                "200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object"}}}}
            },
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
        "由 TestMaster 自动生成的 API 测试代码",
        '"""',
        "import requests",
        "import json",
        "",
        "",
    ]

    for i, case in enumerate(cases):
        method = case.get("method", "GET").upper()
        url = case.get("url", "")
        headers = case.get("headers", {})
        payload = case.get("payload")
        body_type = case.get("body_type", "none")
        name = case.get("name", f"test_case_{i + 1}")

        # 函数名
        func_name = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower()).strip("_")
        if not func_name:
            func_name = f"test_case_{i + 1}"

        lines.append(f"def {func_name}():")
        lines.append(f'    """{name}"""')
        lines.append(f'    url = "{url}"')

        if headers:
            lines.append(f"    headers = {json.dumps(headers, ensure_ascii=False)}")
        else:
            lines.append("    headers = {}")

        if payload and method in ("POST", "PUT", "PATCH"):
            if body_type == "form-data":
                lines.append(f"    data = {json.dumps(payload, ensure_ascii=False)}")
                lines.append(f"    response = requests.{method.lower()}(url, headers=headers, data=data)")
            elif body_type == "graphql":
                graphql_body = {"query": payload.get("query", "") if isinstance(payload, dict) else str(payload)}
                if isinstance(payload, dict) and "variables" in payload:
                    graphql_body["variables"] = payload["variables"]
                lines.append(f"    payload = {json.dumps(graphql_body, ensure_ascii=False)}")
                lines.append(f"    response = requests.{method.lower()}(url, headers=headers, json=payload)")
            else:
                lines.append(f"    payload = {json.dumps(payload, ensure_ascii=False)}")
                lines.append(f"    response = requests.{method.lower()}(url, headers=headers, json=payload)")
        else:
            lines.append(f"    response = requests.{method.lower()}(url, headers=headers)")

        lines.append('    print(f"Status: {response.status_code}")')
        lines.append('    print(f"Body: {response.text[:500]}")')
        lines.append("    return response")
        lines.append("")
        lines.append("")

    return "\n".join(lines)


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
            v_escaped = str(v).replace('"', '\\"')
            parts.append(f'  -H "{k}: {v_escaped}"')

        if payload and method in ("POST", "PUT", "PATCH"):
            if body_type == "form-data" and isinstance(payload, dict):
                for k, v in payload.items():
                    v_escaped = str(v).replace('"', '\\"')
                    parts.append(f'  -d "{k}={v_escaped}"')
            else:
                body_str = (
                    json.dumps(payload, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
                )
                # 转义 body 中的单引号
                body_escaped = body_str.replace("'", "'\\''")
                parts.append(f"  --data-raw '{body_escaped}'")

        curls.append(" \\\n".join(parts))

    return curls


def _json_to_schema(value: Any, _depth: int = 0) -> Dict:
    """将 JSON 值转换为 OpenAPI Schema（带深度限制防止循环引用）"""
    if _depth > 10:
        return {"type": "object"}

    if isinstance(value, dict):
        properties = {}
        for k, v in value.items():
            properties[k] = _json_to_schema(v, _depth + 1)
        return {"type": "object", "properties": properties}
    elif isinstance(value, list):
        if value:
            return {"type": "array", "items": _json_to_schema(value[0], _depth + 1)}
        return {"type": "array", "items": {}}
    elif isinstance(value, bool):
        return {"type": "boolean", "example": value}
    elif isinstance(value, int):
        return {"type": "integer", "example": value}
    elif isinstance(value, float):
        return {"type": "number", "example": value}
    elif value is None:
        return {"type": "string", "nullable": True, "example": None}
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


def export_enhanced_api_doc(
    cases: List[Dict],
    execution_history: Optional[Dict[int, List[Dict]]] = None,
    mock_rules: Optional[Dict[str, Dict]] = None,
    scenarios: Optional[List[Dict]] = None,
    performance_metrics: Optional[Dict[int, Dict]] = None,
    global_variables: Optional[List[Dict]] = None,
    title: str = "TestMaster API",
    version: str = "1.0.0",
) -> Dict:
    """
    导出增强的 API 文档（超越 Apifox 的核心功能）

    联动特性：
    - 真实执行数据示例（从执行历史提取）
    - Mock 服务关联提示
    - 场景业务流程展示
    - 性能指标展示（来自 JMeter 测试）
    - 全局变量引用提示
    """
    paths = {}
    tags_set = set()

    for case in cases:
        url = case.get("url", "")
        method = case.get("method", "GET").lower()
        name = case.get("name", "")
        description = case.get("description", "")
        case_id = case.get("id")
        group_name = case.get("group_name", "default")

        # 优先使用预处理好的 path，避免重复解析导致不一致
        path = case.get("path")
        if not path:
            parsed = urlparse(url)
            path = parsed.path or url
            if not path.startswith("/"):
                path = "/" + path

        if path not in paths:
            paths[path] = {}

        # 同一个 path+method 可能存在多个用例，仅保留第一个（避免覆盖）
        if method in paths[path]:
            continue

        tags_set.add(group_name)

        # ========== 构建请求体 ==========
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

            schema = _json_to_schema(payload)
            example_value = payload

            request_body = {
                "description": description or f"{name} 的请求体",
                "required": True,
                "content": {
                    content_type: {
                        "schema": schema,
                        "example": example_value,
                    }
                },
            }

        # ========== 构建参数 ==========
        parameters = []
        params = case.get("params")
        if params and isinstance(params, dict):
            for k, v in params.items():
                parameters.append(
                    {
                        "name": k,
                        "in": "query",
                        "required": False,
                        "schema": {"type": _guess_type(v)},
                        "example": v,
                        "description": f"查询参数: {k}",
                    }
                )

        headers = case.get("headers")
        if headers and isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() not in ("content-type", "authorization"):
                    parameters.append(
                        {
                            "name": k,
                            "in": "header",
                            "schema": {"type": "string"},
                            "example": v,
                        }
                    )

        # ========== 构建响应（从真实执行历史提取） ==========
        responses = {}
        case_history = execution_history.get(case_id, []) if execution_history else []

        if case_history:
            for hist in case_history:
                status_code = hist.get("status_code", 200)
                response_data = hist.get("response_data")
                execution_time = hist.get("execution_time")

                response_schema = _json_to_schema(response_data) if response_data else {"type": "object"}
                response_desc = hist.get("status", "成功")

                responses[str(status_code)] = {
                    "description": response_desc,
                    "content": {
                        "application/json": {
                            "schema": response_schema,
                            "example": response_data,
                        }
                    },
                    "x-execution-time-ms": execution_time,
                }

        if not responses:
            responses = {
                "200": {"description": "成功", "content": {"application/json": {"schema": {"type": "object"}}}}
            }

        # ========== 构建 operation ==========
        operation = {
            "summary": name,
            "description": description,
            "operationId": f"{method}_{path.replace('/', '_').strip('_')}",
            "tags": [group_name],
            "responses": responses,
        }

        if parameters:
            operation["parameters"] = parameters
        if request_body:
            operation["requestBody"] = request_body

        # ========== x-testmaster 扩展字段（联动数据） ==========
        x_testmaster = {}

        # 1. Mock 服务关联（支持通配符路径匹配）
        if mock_rules:
            mock_key = f"{method.upper()} {path}"
            # 先精确匹配
            mock_info = mock_rules.get(mock_key)
            # 如果精确匹配失败，尝试通配符匹配
            if not mock_info:
                for rule_key, rule_info in mock_rules.items():
                    # rule_key 格式: "METHOD /path"，方法和方法之间只有一个空格
                    space_idx = rule_key.find(" ")
                    if space_idx == -1:
                        continue
                    rule_method = rule_key[:space_idx]
                    rule_path = rule_key[space_idx + 1 :]
                    if rule_method != method.upper():
                        continue
                    # 支持 * 通配符匹配
                    if "*" in rule_path:
                        if fnmatch.fnmatch(path, rule_path):
                            mock_info = rule_info
                            break
            if mock_info:
                x_testmaster["mock"] = {
                    "enabled": True,
                    "project_name": mock_info.get("project_name"),
                    "rule_name": mock_info.get("rule_name"),
                    "mock_url": f"/api/mock/{mock_info.get('base_url_slug')}{path}",
                }

        # 2. 场景流程关联
        if scenarios and case_id is not None:
            related_scenarios = [
                s for s in scenarios if any(step.get("api_case_id") == case_id for step in s.get("steps", []))
            ]
            if related_scenarios:
                x_testmaster["scenarios"] = []
                for s in related_scenarios:
                    # 找到该用例在场景中的步骤顺序，使用默认值避免 StopIteration
                    matching_steps = [
                        step.get("step_order", 0) for step in s.get("steps", []) if step.get("api_case_id") == case_id
                    ]
                    step_order = matching_steps[0] if matching_steps else 0
                    x_testmaster["scenarios"].append(
                        {
                            "id": s["id"],
                            "name": s["name"],
                            "description": s.get("description"),
                            "step_order": step_order,
                        }
                    )

        # 3. 性能指标（来自 JMeter 测试）
        if performance_metrics and case_id in performance_metrics:
            perf = performance_metrics[case_id]
            x_testmaster["performance"] = {
                "avg_response_time": perf.get("avg_response_time"),
                "p95_response_time": perf.get("p95_response_time"),
                "p99_response_time": perf.get("p99_response_time"),
                "requests_per_second": perf.get("requests_per_second"),
                "error_rate": perf.get("error_rate"),
            }

        # 4. 全局变量引用提示
        if global_variables:
            var_refs = []
            url_text = url
            # payload 可能是 dict/list/str/None，统一转为字符串进行匹配
            if payload is not None:
                payload_text = (
                    json.dumps(payload, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
                )
            else:
                payload_text = ""
            headers_text = json.dumps(headers, ensure_ascii=False) if headers and isinstance(headers, dict) else ""
            all_text = f"{url_text} {payload_text} {headers_text}"

            for var in global_variables:
                var_name = var.get("name", "")
                # 匹配系统实际使用的 {{var_name}} 格式
                if f"{{{{{var_name}}}}}" in all_text or f"{{var_name}}" in all_text:
                    var_refs.append(
                        {
                            "name": var_name,
                            "description": var.get("description"),
                            "is_encrypted": var.get("is_encrypted", False),
                        }
                    )

            if var_refs:
                x_testmaster["global_variables"] = var_refs

        if x_testmaster:
            operation["x-testmaster"] = x_testmaster

        paths[path][method] = operation

    # ========== 构建 tags ==========
    tags = []
    for tag_name in sorted(tags_set):
        tag_info = {"name": tag_name}
        if scenarios:
            related = [s for s in scenarios if s.get("group_name") == tag_name]
            if related:
                tag_info["description"] = f"包含 {len(related)} 个业务流程"
        tags.append(tag_info)

    return {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": "由 TestMaster 自动生成的 API 文档 - 文档即用例，用例即文档",
        },
        "tags": tags,
        "paths": paths,
        "x-testmaster-info": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(cases),
            "total_scenarios": len(scenarios) if scenarios else 0,
            "features": [
                "真实执行数据示例",
                "Mock 服务关联",
                "场景流程展示",
                "性能指标展示",
                "全局变量引用提示",
            ],
        },
    }
