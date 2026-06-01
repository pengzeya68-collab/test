"""
AI 智能生成测试用例服务

从 Swagger/OpenAPI 文档自动分析接口，利用 LLM 生成带断言、变量提取、场景链的完整测试用例。
"""

import json
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.utils.ai_config import (
    load_ai_config,
    resolve_ai_params,
    call_llm_json,
)

_logger = logging.getLogger(__name__)


class AITestCaseGenerator:
    """AI 测试用例生成器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_swagger(self, swagger_data: dict) -> dict:
        """解析 Swagger 文档，提取接口信息"""
        info = swagger_data.get("info", {})
        paths = swagger_data.get("paths", {})
        base_url = ""
        servers = swagger_data.get("servers", [])
        if servers:
            base_url = servers[0].get("url", "")

        # 提取 components/schemas 中的模型定义
        schemas = swagger_data.get("components", {}).get("schemas", {})
        if not schemas:
            schemas = swagger_data.get("definitions", {})

        apis = []
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() not in {
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "PATCH",
                    "HEAD",
                    "OPTIONS",
                }:
                    continue

                # 提取参数
                params = []
                for p in details.get("parameters", []):
                    params.append(
                        {
                            "name": p.get("name", ""),
                            "in": p.get("in", ""),
                            "required": p.get("required", False),
                            "type": (p.get("schema") or {}).get("type", p.get("type", "string")),
                            "description": p.get("description", ""),
                        }
                    )

                # 提取请求体 schema
                request_body = None
                rb = details.get("requestBody", {})
                if rb:
                    content = rb.get("content", {})
                    for ct, ct_detail in content.items():
                        schema = (ct_detail.get("schema") or {})
                        request_body = {"content_type": ct, "schema": schema}
                        break

                # 提取响应 schema
                responses = {}
                for status, resp in details.get("responses", {}).items():
                    resp_content = resp.get("content", {})
                    for ct, ct_detail in resp_content.items():
                        responses[status] = {
                            "description": resp.get("description", ""),
                            "schema": (ct_detail.get("schema") or {}),
                        }
                        break
                    if status not in responses:
                        responses[status] = {"description": resp.get("description", "")}

                apis.append(
                    {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", details.get("operationId", f"{method.upper()} {path}")),
                        "tags": details.get("tags", []),
                        "params": params,
                        "request_body": request_body,
                        "responses": responses,
                    }
                )

        return {
            "title": info.get("title", "API"),
            "version": info.get("version", ""),
            "base_url": base_url,
            "schemas": schemas,
            "apis": apis,
        }

    def _build_prompt(self, parsed: dict, options: dict) -> str:
        """构建 AI 提示词"""
        max_cases = options.get("max_cases_per_api", 3)
        include_boundary = options.get("include_boundary", True)
        include_auth = options.get("include_auth", True)
        include_chain = options.get("include_chain", True)

        parts = []
        parts.append("你是一个专业的 API 测试用例生成器。根据以下 Swagger/OpenAPI 接口信息，生成高质量的测试用例。")
        parts.append("")
        parts.append("=== API 文档信息 ===")
        parts.append(f"标题: {parsed['title']}")
        parts.append(f"版本: {parsed['version']}")
        parts.append(f"Base URL: {parsed['base_url']}")
        parts.append("")

        if parsed["schemas"]:
            parts.append("=== 数据模型定义 ===")
            for name, schema in list(parsed["schemas"].items())[:20]:  # 限制模型数量
                parts.append(f"【{name}】: {json.dumps(schema, ensure_ascii=False)[:500]}")
            parts.append("")

        parts.append("=== 接口列表 ===")
        for api in parsed["apis"]:
            parts.append(f"\n【{api['method']} {api['path']}】{api['summary']}")
            if api["tags"]:
                parts.append(f"  标签: {', '.join(api['tags'])}")
            if api["params"]:
                parts.append(f"  参数: {json.dumps(api['params'], ensure_ascii=False)}")
            if api["request_body"]:
                rb = api["request_body"]
                parts.append(f"  请求体({rb['content_type']}): {json.dumps(rb['schema'], ensure_ascii=False)[:800]}")
            if api["responses"]:
                for status, resp in api["responses"].items():
                    resp_str = json.dumps(resp, ensure_ascii=False)[:300]
                    parts.append(f"  响应 [{status}]: {resp_str}")

        parts.append("")
        parts.append("=== 生成要求 ===")
        parts.append(f"1. 每个接口最多生成 {max_cases} 个测试用例")
        parts.append(
            "2. 每个用例必须包含: name(名称), method, url, headers, payload(请求体), assert_rules(断言规则), extractors(变量提取), description(描述)"
        )
        parts.append(
            '3. 断言规则格式: [{"field": "响应字段路径", "operator": "equals|contains|gt|lt|gte|lte|regex|json_exists", "expected": "期望值", "description": "描述"}]'
        )
        parts.append(
            '4. 变量提取格式: [{"type": "jsonpath|regex|header", "expression": "表达式", "variable": "变量名"}]'
        )
        if include_boundary:
            parts.append("5. 必须包含边界测试用例：空值、超长字符串、类型错误")
        if include_auth:
            parts.append("6. 必须包含鉴权测试用例：无token请求")
        if include_chain:
            parts.append(
                '7. 如果接口之间有 CRUD 关系，生成场景链(scenarios): [{"name": "场景名", "description": "描述", "steps": [{"api_index": 接口序号从0开始, "description": "步骤描述"}]}]'
            )
        parts.append("")
        parts.append("=== 输出格式 ===")
        parts.append("直接返回以下 JSON 格式，不要有其他文字：")
        parts.append("""{
  "cases": [
    {
      "name": "用例名称",
      "method": "GET/POST/PUT/DELETE",
      "url": "完整URL",
      "headers": {"Content-Type": "application/json"},
      "payload": {"key": "value"},
      "assert_rules": [
        {"field": "$.code", "operator": "equals", "expected": "200", "description": "状态码应为200"}
      ],
      "extractors": [
        {"type": "jsonpath", "expression": "$.data.id", "variable": "created_id"}
      ],
      "description": "用例描述",
      "api_index": 0
    }
  ],
  "scenarios": [
    {
      "name": "CRUD完整流程",
      "description": "创建→查询→修改→删除",
      "steps": [
        {"api_index": 0, "description": "创建资源"},
        {"api_index": 1, "description": "查询详情", "use_variables": {"id": "{{created_id}}"}}
      ]
    }
  ]
}""")
        return "\n".join(parts)

    async def generate(self, swagger_data: dict, options: dict = None) -> dict:
        """从 Swagger 数据生成测试用例"""
        options = options or {}
        parsed = self._parse_swagger(swagger_data)

        if not parsed["apis"]:
            return {"cases": [], "scenarios": [], "message": "未发现可测试的接口"}

        config = await load_ai_config(self.db)
        params = resolve_ai_params(config)

        if not params.api_key:
            return self._generate_fallback(parsed)

        prompt = self._build_prompt(parsed, options)

        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的 API 测试工程师，擅长编写全面的测试用例。只返回 JSON，不要有其他文字。",
                },
                {"role": "user", "content": prompt},
            ]
            result = await call_llm_json(params, messages)
            # 确保返回结构正确
            if "cases" not in result:
                result = {"cases": [], "scenarios": []}
            # 补充 base_url 到 url 中
            for case in result.get("cases", []):
                url = case.get("url", "")
                if url and not url.startswith("http"):
                    case["url"] = parsed["base_url"].rstrip("/") + "/" + url.lstrip("/")
            return result
        except Exception as e:
            _logger.error(f"AI 生成测试用例失败: {e}", exc_info=True)
            return self._generate_fallback(parsed)

    def _generate_fallback(self, parsed: dict) -> dict:
        """无 AI 配置时的规则回退生成"""
        cases = []
        for idx, api in enumerate(parsed["apis"]):
            url = parsed["base_url"].rstrip("/") + api["path"]
            url = re.sub(r"\{(\w+)\}", r"{{\1}}", url)

            headers = {"Content-Type": "application/json"}
            payload = None
            if api["request_body"]:
                payload = self._generate_example_from_schema(api["request_body"]["schema"], parsed.get("schemas", {}))

            # 正向用例
            assert_rules = []
            for status in api.get("responses", {}):
                if status.isdigit() and int(status) < 400:
                    assert_rules.append(
                        {
                            "field": "$",
                            "operator": "json_exists",
                            "expected": "",
                            "description": f"响应应符合 {status} 结构",
                        }
                    )
                    break

            cases.append(
                {
                    "name": f"[正向] {api['summary']}",
                    "method": api["method"],
                    "url": url,
                    "headers": headers,
                    "payload": payload,
                    "assert_rules": assert_rules,
                    "extractors": [],
                    "description": f"正向测试: {api['method']} {api['path']}",
                    "api_index": idx,
                }
            )

            # 无鉴权用例
            cases.append(
                {
                    "name": f"[鉴权] {api['summary']} - 无Token",
                    "method": api["method"],
                    "url": url,
                    "headers": {"Content-Type": "application/json"},
                    "payload": payload,
                    "assert_rules": [
                        {"field": "$", "operator": "json_exists", "expected": "", "description": "应返回 401/403 错误"},
                    ],
                    "extractors": [],
                    "description": f"无 Token 请求 {api['method']} {api['path']}，预期被拒绝",
                    "api_index": idx,
                }
            )

        return {
            "cases": cases,
            "scenarios": [],
            "message": f"规则生成完成（未配置 AI），共 {len(cases)} 个用例。配置 AI 后可生成更智能的用例。",
        }

    def _generate_example_from_schema(self, schema: dict, schemas: dict, _visited: set = None) -> Any:
        """从 OpenAPI schema 生成示例数据"""
        if _visited is None:
            _visited = set()
        if not schema:
            return None
        if "$ref" in schema:
            ref_path = schema["$ref"]
            ref_name = ref_path.split("/")[-1]
            if ref_name in _visited:
                return {}  # 循环引用，返回空对象
            _visited.add(ref_name)
            if ref_name in schemas:
                return self._generate_example_from_schema(schemas[ref_name], schemas, _visited)
            return {}
        if "example" in schema:
            return schema["example"]
        schema_type = schema.get("type", "object")
        if schema_type == "object":
            result = {}
            for prop_name, prop_schema in schema.get("properties", {}).items():
                result[prop_name] = self._generate_example_from_schema(prop_schema, schemas, _visited)
            return result
        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._generate_example_from_schema(items, schemas, _visited)]
        elif schema_type == "string":
            fmt = schema.get("format", "")
            if fmt == "email":
                return "test@example.com"
            if fmt == "date":
                return "2024-01-01"
            if fmt == "date-time":
                return "2024-01-01T00:00:00Z"
            return "string"
        elif schema_type == "integer":
            return 0
        elif schema_type == "number":
            return 0.0
        elif schema_type == "boolean":
            return True
        return None
