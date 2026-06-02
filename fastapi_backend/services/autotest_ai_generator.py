"""
AI 智能生成测试用例服务 - 三阶段批处理架构

Phase 1 - Analyze: 分析 API 文档结构，识别 CRUD 关系和数据依赖
Phase 2 - Generate Cases: 分批调用 AI 生成高质量测试用例（每批 5 个 API）
Phase 3 - Generate Scenarios: 基于分析结果和用例生成场景链

通过 Celery 异步执行，支持进度轮询。
"""

import asyncio
import json
import logging
import re
import time
import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.utils.ai_config import (
    load_ai_config,
    resolve_ai_params,
    call_llm_json,
    AIParams,
)

_logger = logging.getLogger(__name__)

BATCH_SIZE = 5
BATCH_TIMEOUT = 120
MAX_RETRIES = 2
RETRY_BASE_DELAY = 5  # 秒


class RateLimitExceededError(Exception):
    """AI API 5小时窗口限额耗尽，无法继续"""
    def __init__(self, message: str, provider: str = ""):
        super().__init__(message)
        self.provider = provider


async def _call_llm_with_retry(params: AIParams, messages: list, timeout: int = None, progress_callback=None) -> dict:
    """带 429 限流重试的 LLM JSON 调用

    区分两种 429:
    - RPM 限流（每分钟请求数超限）: 短暂等待后重试
    - 窗口限额耗尽（如 MiniMax 5小时窗口）: 抛出 RateLimitExceededError，不无意义重试
    """
    import asyncio

    effective_timeout = timeout or params.timeout
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            retry_params = AIParams(
                api_key=params.api_key,
                base_url=params.base_url,
                model=params.model,
                provider=params.provider,
                timeout=effective_timeout,
                max_tokens=params.max_tokens,
                temperature=params.temperature,
                group_id=params.group_id,
            )
            return await call_llm_json(retry_params, messages)
        except Exception as e:
            last_error = e
            error_str = str(e)

            if "429" in error_str or "rate_limit" in error_str.lower():
                # MiniMax 2056 = 5小时窗口限额耗尽，重试无意义
                if "usage limit exceeded" in error_str.lower() or "2056" in error_str:
                    _logger.error("AI API 窗口限额耗尽 (429/2056)，需要等待窗口重置: %s", error_str[:300])
                    raise RateLimitExceededError(
                        f"AI API 窗口限额已耗尽（{params.provider} 返回 usage limit exceeded），"
                        f"需要等待 5 小时窗口重置后重试。建议：1) 等待窗口重置 2) 换用其他 AI 服务 3) 减少接口数量",
                        provider=params.provider,
                    )

                # 普通 RPM 限流 - 指数退避重试
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                _logger.warning("AI API RPM 限流 (429)，第 %d/%d 次重试，等待 %ds: %s",
                                attempt + 1, MAX_RETRIES, delay, error_str[:200])
                if progress_callback:
                    await progress_callback(f"AI 限流，等待 {delay}s 后重试 ({attempt+1}/{MAX_RETRIES})...")
                await asyncio.sleep(delay)
                continue
            # 其他错误不重试
            raise

    raise last_error


class AITestCaseGenerator:
    """AI 测试用例生成器"""

    def __init__(self, db: AsyncSession = None):
        self.db = db

    # ------------------------------------------------------------------
    # Swagger 解析（保留原有逻辑）
    # ------------------------------------------------------------------

    def _parse_swagger(self, swagger_data: dict) -> dict:
        """解析 Swagger 文档，提取接口信息（含安全约束、枚举、范围等）"""
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

        # 提取全局安全定义
        security_schemes = swagger_data.get("components", {}).get("securitySchemes", {})
        global_security = swagger_data.get("security", [])

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

                # 提取参数（含枚举、范围、默认值等约束）
                params = []
                for p in details.get("parameters", []):
                    schema = p.get("schema") or {}
                    param_info = {
                        "name": p.get("name", ""),
                        "in": p.get("in", ""),
                        "required": p.get("required", False),
                        "type": schema.get("type", p.get("type", "string")),
                        "description": p.get("description", ""),
                    }
                    # 提取约束信息
                    if schema.get("enum"):
                        param_info["enum"] = schema["enum"]
                    if schema.get("minimum") is not None:
                        param_info["minimum"] = schema["minimum"]
                    if schema.get("maximum") is not None:
                        param_info["maximum"] = schema["maximum"]
                    if schema.get("minLength") is not None:
                        param_info["minLength"] = schema["minLength"]
                    if schema.get("maxLength") is not None:
                        param_info["maxLength"] = schema["maxLength"]
                    if schema.get("pattern"):
                        param_info["pattern"] = schema["pattern"]
                    if schema.get("default") is not None:
                        param_info["default"] = schema["default"]
                    if p.get("deprecated"):
                        param_info["deprecated"] = True
                    params.append(param_info)

                # 提取请求体 schema（含约束）
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

                # 提取接口级别的安全要求
                api_security = details.get("security", global_security)
                requires_auth = bool(api_security) if api_security is not None else bool(global_security)

                apis.append(
                    {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", details.get("operationId", f"{method.upper()} {path}")),
                        "tags": details.get("tags", []),
                        "params": params,
                        "request_body": request_body,
                        "responses": responses,
                        "requires_auth": requires_auth,
                        "deprecated": details.get("deprecated", False),
                    }
                )

        return {
            "title": info.get("title", "API"),
            "version": info.get("version", ""),
            "base_url": base_url,
            "schemas": schemas,
            "apis": apis,
            "security_schemes": security_schemes,
        }

    # ------------------------------------------------------------------
    # Schema 示例数据生成（保留原有逻辑）
    # ------------------------------------------------------------------

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
                return {}
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

    # ------------------------------------------------------------------
    # 规则回退生成（保留原有逻辑）
    # ------------------------------------------------------------------

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
            assert_rules = [
                {"field": "status_code", "operator": "range", "expected": "2xx/3xx"},
            ]
            # 如果有响应定义，添加响应体断言
            for status, resp in api.get("responses", {}).items():
                if str(status).isdigit() and int(status) < 400:
                    resp_schema = resp.get("schema", {})
                    if resp_schema.get("type") == "object" or resp_schema.get("properties"):
                        assert_rules.append(
                            {"field": "$", "operator": "not_empty", "expected": ""}
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

            # 鉴权用例 - 仅对需鉴权接口生成
            if api.get("requires_auth"):
                cases.append(
                    {
                        "name": f"[鉴权] {api['summary']} - 无Token",
                        "method": api["method"],
                        "url": url,
                        "headers": {"Content-Type": "application/json"},
                        "payload": payload,
                        "assert_rules": [
                            {"field": "status_code", "operator": "range", "expected": "4xx"},
                            {"field": "$.detail", "operator": "not_empty", "expected": ""},
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

    # ------------------------------------------------------------------
    # Phase 1 - 分析 API 文档结构
    # ------------------------------------------------------------------

    def _build_analyze_prompt(self, batch_apis: list, parsed: dict, previous_analysis: dict = None) -> str:
        """构建 Phase 1 分析提示词（分批版，每批只分析 BATCH_SIZE 个 API）

        Args:
            batch_apis: 当前批次的 API 列表（已含 _global_index）
            parsed: 完整解析结果
            previous_analysis: 之前批次累积的分析结果，供 AI 参考已有关系
        """
        parts = []
        parts.append(f"分析以下API文档片段，识别CRUD关系和数据依赖。标题:{parsed['title']} 本批接口数:{len(batch_apis)}")
        parts.append("")

        # 当前批次接口列表
        for api in batch_apis:
            idx = api.get("_global_index", 0)
            line = f"[{idx}] {api['method']} {api['path']} {api.get('summary', '')}"
            if api.get("tags"):
                line += f" [{','.join(api['tags'])}]"
            parts.append(line)

        # 如果有之前批次的分析结果，提供参考
        if previous_analysis:
            prev_groups = previous_analysis.get("resource_groups", [])
            prev_rels = previous_analysis.get("relationships", [])
            prev_flow = previous_analysis.get("data_flow", [])
            if prev_groups:
                parts.append("")
                parts.append("已识别的资源分组（请在此基础上补充，不要重复）:")
                for g in prev_groups[:15]:
                    parts.append(f"  - {g.get('resource_name', '')}({g.get('resource_name_en', '')}) 接口{g.get('api_indices', [])}")
            if prev_rels:
                parts.append("")
                parts.append("已识别的接口关系（请在此基础上补充，不要重复）:")
                for r in prev_rels[:10]:
                    parts.append(f"  - [{r.get('from_api')}]->[{r.get('to_api')}]: {r.get('description', '')}")
            if prev_flow:
                parts.append("")
                parts.append("已识别的数据流（请在此基础上补充，不要重复）:")
                for f in prev_flow[:10]:
                    parts.append(f"  - [{f.get('source_api')}].{f.get('source_field')})->[{f.get('target_api')}].{f.get('target_param')} var:{f.get('variable_name', '')}")

        parts.append("")
        parts.append("输出JSON格式（只包含本批新增的分析结果，与之前不重复）:")
        parts.append('{"resource_groups":[{"resource_name":"用户","resource_name_en":"user","api_indices":[0,1,2,3],"crud_mapping":{"create":0,"read":1,"update":2,"delete":3}}],"relationships":[{"from_api":0,"to_api":1,"type":"id_dependency","description":"创建返回ID用于查询"}],"auth_pattern":{"type":"Bearer Token","login_api_index":null,"token_field":"$.data.token"},"data_flow":[{"source_api":0,"source_field":"$.data.id","target_api":1,"target_param":"id","variable_name":"user_id"}]}')
        return "\n".join(parts)

    async def _phase_analyze(self, parsed: dict, params: AIParams) -> dict:
        """Phase 1: 分析全部 API 文档结构（兼容旧调用方式，内部一次性分析）"""
        prompt = self._build_analyze_prompt(parsed["apis"], parsed)
        messages = [
            {
                "role": "system",
                "content": "你是API架构分析师。只返回JSON，不要其他文字。",
            },
            {"role": "user", "content": prompt},
        ]
        result = await _call_llm_with_retry(params, messages)
        # 确保关键字段存在
        result.setdefault("resource_groups", [])
        result.setdefault("relationships", [])
        result.setdefault("auth_pattern", {"type": "unknown"})
        result.setdefault("data_flow", [])
        return result

    async def _phase_analyze_batch(
        self, batch_apis: list, parsed: dict, params: AIParams, previous_analysis: dict = None
    ) -> dict:
        """Phase 1 分批版: 分析当前批次的 API，返回本批分析结果

        Args:
            batch_apis: 当前批次的 API 列表（已含 _global_index）
            parsed: 完整解析结果
            params: AI 参数
            previous_analysis: 之前批次累积的分析结果
        """
        prompt = self._build_analyze_prompt(batch_apis, parsed, previous_analysis)
        messages = [
            {
                "role": "system",
                "content": "你是API架构分析师。只返回JSON，不要其他文字。只输出本批新增的分析结果。",
            },
            {"role": "user", "content": prompt},
        ]
        result = await _call_llm_with_retry(params, messages)
        result.setdefault("resource_groups", [])
        result.setdefault("relationships", [])
        result.setdefault("auth_pattern", {"type": "unknown"})
        result.setdefault("data_flow", [])
        return result

    @staticmethod
    def _merge_analysis(accumulated: dict, new_batch: dict) -> dict:
        """合并两批分析结果，去重并累积"""
        # 合并 resource_groups
        existing_names = {g.get("resource_name_en") for g in accumulated.get("resource_groups", [])}
        for g in new_batch.get("resource_groups", []):
            if g.get("resource_name_en") not in existing_names:
                accumulated.setdefault("resource_groups", []).append(g)
                existing_names.add(g.get("resource_name_en"))

        # 合并 relationships（简单追加，不去重）
        accumulated.setdefault("relationships", []).extend(new_batch.get("relationships", []))

        # 合并 data_flow
        accumulated.setdefault("data_flow", []).extend(new_batch.get("data_flow", []))

        # auth_pattern: 后来的覆盖之前的（通常所有批次一致）
        if new_batch.get("auth_pattern"):
            accumulated["auth_pattern"] = new_batch["auth_pattern"]

        return accumulated

    # ------------------------------------------------------------------
    # Phase 2 - 分批生成测试用例
    # ------------------------------------------------------------------

    def _build_case_generation_prompt(
        self,
        batch_apis: list,
        parsed: dict,
        analysis: dict,
        options: dict,
    ) -> str:
        """构建 Phase 2 用例生成提示词 - 精确匹配系统格式"""
        max_cases = options.get("max_cases_per_api", 4)
        include_boundary = options.get("include_boundary", True)
        include_auth = options.get("include_auth", True)

        # 接口关系摘要
        relationships_text = ""
        for rel in analysis.get("relationships", [])[:10]:
            relationships_text += f"[{rel.get('from_api')}]->[{rel.get('to_api')}]: {rel.get('description', '')}\n"
        for flow in analysis.get("data_flow", [])[:10]:
            relationships_text += f"[{flow.get('source_api')}].{flow.get('source_field')})->[{flow.get('target_api')}].{flow.get('target_param')} var:{flow.get('variable_name', '')}\n"

        parts = []
        parts.append(f"为以下{len(batch_apis)}个接口生成测试用例，每接口最多{max_cases}个。")
        parts.append("")

        # 接口信息 - 含约束信息
        for idx, api in enumerate(batch_apis):
            global_idx = api.get("_global_index", idx)
            auth_mark = " [需鉴权]" if api.get("requires_auth") else ""
            deprec_mark = " [已废弃]" if api.get("deprecated") else ""
            line = f"[{global_idx}] {api['method']} {api['path']} {api.get('summary', '')}{auth_mark}{deprec_mark}"
            parts.append(line)
            if api.get("params"):
                try:
                    parts.append(f"  参数:{json.dumps(api['params'], ensure_ascii=False, default=str)[:400]}")
                except Exception:
                    pass
            if api.get("request_body"):
                rb = api["request_body"]
                try:
                    parts.append(f"  请求体:{json.dumps(rb.get('schema', {}), ensure_ascii=False, default=str)[:500]}")
                except Exception:
                    pass
            if api.get("responses"):
                for status, resp in api["responses"].items():
                    try:
                        resp_str = json.dumps(resp, ensure_ascii=False, default=str)[:200]
                    except Exception:
                        resp_str = str(resp)[:200]
                    parts.append(f"  响应[{status}]:{resp_str}")

        if relationships_text:
            parts.append(f"\n接口关系:\n{relationships_text}")

        # 严格格式要求
        parts.append("")
        parts.append("=== 严格输出格式要求 ===")
        parts.append("")
        parts.append("1.断言格式(必须严格遵守):")
        parts.append('  {"field":"status_code","operator":"range","expected":"2xx/3xx"}')
        parts.append('  {"field":"$.data.id","operator":"regex","expected":"^\\\\d+$"}')
        parts.append('  {"field":"$.detail","operator":"not_empty","expected":""}')
        parts.append("  field支持: status_code, $.xxx(JSONPath), response_time")
        parts.append("  operator支持: range, equals, not_equals, contains, not_contains, regex, not_empty, empty, exists, not_exists, gt, lt, gte, lte")
        parts.append("  range值: 2xx/3xx(成功), 4xx(客户端错误), 5xx(服务端错误), 2xx, 3xx")
        parts.append("")
        parts.append("2.提取器格式(必须严格遵守):")
        parts.append('  {"extractorType":"jsonpath","expression":"$.data.id","variableName":"user_id","defaultValue":""}')
        parts.append("  extractorType支持: jsonpath, regex, header")
        parts.append("  变量名用variableName(不是variable/var_name)")
        parts.append("")
        parts.append("3.用例类型与断言规则:")
        parts.append("  正向用例: status_code range 2xx/3xx + 业务字段断言")
        parts.append("  鉴权用例: 不带Authorization头, status_code range 4xx + $.detail not_empty")
        parts.append("  异常用例: 缺少必填参数/超出范围/格式错误, status_code equals 400/422 + 错误字段断言")
        parts.append("  边界用例: 参数取边界值(minimum/maxLength等), status_code range 2xx/3xx 或 equals 422")
        parts.append("")
        parts.append("4.其他规则:")
        parts.append("  - 创建类接口必须提取ID到变量, 登录类提取token")
        parts.append("  - URL中的路径参数用{{变量名}}替换, 如 /api/users/{{user_id}}")
        parts.append("  - 鉴权接口的headers必须包含 Authorization: Bearer {{auth_token}}")
        parts.append("  - 有enum约束的参数,正向用合法值,异常用非法值")
        parts.append("  - 有minimum/maximum的参数,边界用边界值±1")
        parts.append("")
        parts.append("输出JSON:")
        parts.append('{"cases":[{"name":"[正向]创建用户","method":"POST","url":"/api/users","headers":{"Content-Type":"application/json","Authorization":"Bearer {{auth_token}}"},"payload":{"username":"testuser01","password":"Test@123456"},"assert_rules":[{"field":"status_code","operator":"range","expected":"2xx/3xx"},{"field":"$.code","operator":"equals","expected":"0"},{"field":"$.data.id","operator":"regex","expected":"^\\\\d+$"}],"extractors":[{"extractorType":"jsonpath","expression":"$.data.id","variableName":"user_id","defaultValue":""}],"description":"正常注册","api_index":0},{"name":"[鉴权]创建用户-无Token","method":"POST","url":"/api/users","headers":{"Content-Type":"application/json"},"payload":{"username":"testuser01","password":"Test@123456"},"assert_rules":[{"field":"status_code","operator":"range","expected":"4xx"},{"field":"$.detail","operator":"not_empty","expected":""}],"extractors":[],"description":"无Token请求应被拒绝","api_index":0},{"name":"[异常]创建用户-缺少必填","method":"POST","url":"/api/users","headers":{"Content-Type":"application/json","Authorization":"Bearer {{auth_token}}"},"payload":{},"assert_rules":[{"field":"status_code","operator":"equals","expected":"422"},{"field":"$.detail","operator":"not_empty","expected":""}],"extractors":[],"description":"缺少必填字段","api_index":0}]}')

        if not include_boundary:
            parts.append("不生成边界用例。")
        if not include_auth:
            parts.append("不生成鉴权用例。")

        return "\n".join(parts)

    async def _phase_generate_cases(
        self,
        parsed: dict,
        analysis: dict,
        options: dict,
        params: AIParams,
        progress_callback=None,
        task_id: str = None,
        task_context: dict = None,
    ) -> list:
        """Phase 2: 分批生成测试用例

        Args:
            task_id: 任务ID，用于取消检查和AI配置重载。如果为None则不检查。
            task_context: {"start_time", "total_apis", "total_batches"} 用于实时保存用例到task_store
        """
        apis = parsed["apis"]
        total_apis = len(apis)
        total_batches = (total_apis + BATCH_SIZE - 1) // BATCH_SIZE
        all_cases = []

        async def save_cases_now(api_idx: int):
            """每生成完一个接口的用例就立即保存到 task_store"""
            if not task_context or not task_id:
                return
            start_time = task_context["start_time"]
            t_apis = task_context["total_apis"]
            t_batches = task_context["total_batches"]
            await _update_progress(
                task_id,
                status="PROGRESS",
                progress=0.10 + 0.80 * len(all_cases) / max(t_apis * 3, 1),
                phase="generating_cases",
                phase_label=f"正在生成测试用例 ({len(all_cases)} 个用例)...",
                total_apis=t_apis,
                processed_apis=min(api_idx + 1, t_apis),
                total_batches=t_batches,
                current_batch=(api_idx // BATCH_SIZE) + 1,
                cases=list(all_cases),
                start_time=start_time,
            )

        for batch_idx in range(total_batches):
            # 每批次前检查取消标志
            if task_id:
                if await _check_cancelled(task_id):
                    _logger.info("任务 %s 被用户取消，停止生成，已生成 %d 个用例", task_id, len(all_cases))
                    raise asyncio.CancelledError("任务被用户取消")

                # 每批次重新加载 AI 配置，让后管模型切换实时生效
                reloaded = await _reload_ai_params(task_id)
                if reloaded and reloaded.api_key:
                    params = AIParams(
                        api_key=reloaded.api_key,
                        base_url=reloaded.base_url,
                        model=reloaded.model,
                        provider=reloaded.provider,
                        timeout=max(reloaded.timeout, 120),
                        max_tokens=max(reloaded.max_tokens, 4096),
                        temperature=reloaded.temperature,
                        group_id=reloaded.group_id,
                    )
                    _logger.info("任务 %s 批次 %d 重载 AI 配置: provider=%s model=%s",
                                 task_id, batch_idx + 1, params.provider, params.model)

            start = batch_idx * BATCH_SIZE
            end = min(start + BATCH_SIZE, total_apis)
            batch = apis[start:end]

            # 给每个 API 加上全局索引
            batch_with_index = []
            for i, api in enumerate(batch):
                api_copy = dict(api)
                api_copy["_global_index"] = start + i
                batch_with_index.append(api_copy)

            prompt = self._build_case_generation_prompt(
                batch_with_index, parsed, analysis, options
            )
            messages = [
                {
                    "role": "system",
                    "content": "你是API测试工程师。只返回JSON，不要其他文字。严格规则：1)每个用例必须有status_code断言(正向range 2xx/3xx,鉴权range 4xx,异常equals具体码) 2)断言field用status_code或$.xxx(JSONPath) 3)提取器用extractorType和variableName(不是type/variable) 4)鉴权用例不带Authorization头",
                },
                {"role": "user", "content": prompt},
            ]

            try:
                result = await _call_llm_with_retry(params, messages, timeout=BATCH_TIMEOUT)
                batch_cases = result.get("cases", [])
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _logger.error("批次 %d AI 生成失败: %s", batch_idx + 1, e, exc_info=True)
                batch_cases = []

            # 补充 base_url 到 url 中
            for case in batch_cases:
                url = case.get("url", "")
                if url and not url.startswith("http"):
                    case["url"] = parsed["base_url"].rstrip("/") + "/" + url.lstrip("/")

            # 按 api_index 分组，逐个接口保存
            api_cases = {}
            for case in batch_cases:
                api_idx = case.get("api_index", 0)
                if api_idx not in api_cases:
                    api_cases[api_idx] = []
                api_cases[api_idx].append(case)

            # 逐个接口 extend 并立即保存到 task_store
            for api_idx, cases_for_api in api_cases.items():
                all_cases.extend(cases_for_api)
                await save_cases_now(api_idx)

            # 进度回调
            if progress_callback:
                await progress_callback(batch_idx, total_batches, len(all_cases))

            _logger.info(
                "Phase 2 批次 %d/%d 完成，本批 %d 个用例，累计 %d 个",
                batch_idx + 1,
                total_batches,
                len(batch_cases),
                len(all_cases),
            )

        return all_cases

    # ------------------------------------------------------------------
    # Phase 3 - 生成场景链
    # ------------------------------------------------------------------

    def _build_scenario_prompt(self, parsed: dict, analysis: dict, all_cases: list) -> str:
        """构建 Phase 3 场景链生成提示词（精简版）"""
        parts = []
        parts.append("根据以下分析结果和用例，设计测试场景链。")

        # 接口关系 - 精简
        for rel in analysis.get("relationships", [])[:10]:
            parts.append(f"关系:[{rel.get('from_api')}]->[{rel.get('to_api')}]: {rel.get('description', '')}")
        for flow in analysis.get("data_flow", [])[:10]:
            parts.append(f"数据流:[{flow.get('source_api')}].{flow.get('source_field')})->[{flow.get('target_api')}].{flow.get('target_param')} var:{flow.get('variable_name', '')}")

        # 资源分组 - 精简
        for group in analysis.get("resource_groups", [])[:10]:
            parts.append(f"资源:{group.get('resource_name', '')}({group.get('resource_name_en', '')}) 接口{group.get('api_indices', [])}")

        # 已有用例摘要 - 限制数量
        parts.append(f"\n已有{len(all_cases)}个用例:")
        for case in all_cases[:30]:
            parts.append(f"- [{case.get('api_index', '?')}] {case.get('name', '')}")
        if len(all_cases) > 30:
            parts.append(f"... 共{len(all_cases)}个")

        parts.append("")
        parts.append("为每个资源生成CRUD场景链，步骤引用api_index，用use_variables传变量。")
        parts.append("输出JSON:")
        parts.append('{"scenarios":[{"name":"用户CRUD流程","description":"创建→查询→更新→删除","steps":[{"api_index":0,"description":"创建用户","use_variables":{}},{"api_index":1,"description":"查询用户","use_variables":{"id":"{{user_id}}"}}]}]}')
        return "\n".join(parts)

    async def _phase_generate_scenarios(
        self, parsed: dict, analysis: dict, all_cases: list, params: AIParams
    ) -> list:
        """Phase 3: 生成场景链"""
        prompt = self._build_scenario_prompt(parsed, analysis, all_cases)
        messages = [
            {
                "role": "system",
                "content": "你是API测试工程师。只返回JSON，不要其他文字。",
            },
            {"role": "user", "content": prompt},
        ]
        try:
            result = await _call_llm_with_retry(params, messages)
            return result.get("scenarios", [])
        except Exception as e:
            _logger.error("Phase 3 场景生成失败: %s", e, exc_info=True)
            return []

    # ------------------------------------------------------------------
    # 同步入口（兼容旧调用方式，不走 Celery）
    # ------------------------------------------------------------------

    async def generate(self, swagger_data: dict, options: dict = None) -> dict:
        """从 Swagger 数据生成测试用例（同步模式，不走 Celery）"""
        options = options or {}
        parsed = self._parse_swagger(swagger_data)

        if not parsed["apis"]:
            return {"cases": [], "scenarios": [], "message": "未发现可测试的接口"}

        try:
            from fastapi_backend.core.database import AsyncSessionLocal as MainDBSession
            async with MainDBSession() as main_db:
                config = await load_ai_config(main_db)
            params = resolve_ai_params(config)
        except Exception as e:
            _logger.warning("加载 AI 配置失败，使用规则回退: %s", e)
            return self._generate_fallback(parsed)

        if not params.api_key:
            return self._generate_fallback(parsed)

        try:
            # Phase 1
            analysis = await self._phase_analyze(parsed, params)
            # Phase 2
            all_cases = await self._phase_generate_cases(parsed, analysis, options, params)
            # Phase 3
            scenarios = await self._phase_generate_scenarios(parsed, analysis, all_cases, params)

            return {
                "cases": all_cases,
                "scenarios": scenarios,
                "message": f"AI 生成完成，共 {len(all_cases)} 个用例，{len(scenarios)} 个场景",
            }
        except Exception as e:
            _logger.error("AI 生成测试用例失败: %s", e, exc_info=True)
            return self._generate_fallback(parsed)


# ======================================================================
# Celery 异步任务 & 进度管理
# ======================================================================


def create_task_id() -> str:
    """创建 AI 生成任务 ID"""
    return f"ai-gen-{uuid.uuid4().hex[:12]}"


async def _reload_ai_params(task_id: str) -> Optional[AIParams]:
    """每次批次调用前重新加载 AI 配置，让后管模型切换实时生效"""
    try:
        from fastapi_backend.core.database import AsyncSessionLocal as MainDBSession
        async with MainDBSession() as main_db:
            config = await load_ai_config(main_db)
        return resolve_ai_params(config)
    except Exception as e:
        _logger.warning("重载 AI 配置失败 task_id=%s: %s", task_id, e)
        return None


async def _check_cancelled(task_id: str) -> bool:
    """检查任务是否被取消"""
    from fastapi_backend.services.autotest_task_store import is_task_cancelled
    return is_task_cancelled(task_id)


async def _update_progress(task_id: str, **kwargs) -> None:
    """更新任务进度到 task_store"""
    from fastapi_backend.services.autotest_task_store import update_task, get_task

    stored = get_task(task_id) or {"task_id": task_id}
    stored.update(kwargs)
    await update_task(task_id, stored)


async def _run_generation(task_id: str, swagger_data: dict, options: dict) -> None:
    """流水线式异步生成主流程：分析一批→生成一批，实时保存用例

    核心改进：将原来的 "先全部分析再分批生成" 改为 "每批先分析再生成"，
    这样中断时已分析和生成的用例都能保留，不会浪费 token。
    """
    generator = AITestCaseGenerator()
    parsed = generator._parse_swagger(swagger_data)

    if not parsed["apis"]:
        await _update_progress(
            task_id,
            status="completed",
            progress=1.0,
            phase="completed",
            phase_label="完成（无接口）",
            cases=[],
            scenarios=[],
            message="未发现可测试的接口",
        )
        return

    # 加载 AI 配置
    try:
        from fastapi_backend.core.database import AsyncSessionLocal as MainDBSession
        async with MainDBSession() as main_db:
            config = await load_ai_config(main_db)
        params = resolve_ai_params(config)
    except Exception as e:
        _logger.warning("加载 AI 配置失败，使用规则回退: %s", e)
        fallback_result = generator._generate_fallback(parsed)
        await _update_progress(
            task_id,
            status="completed",
            progress=1.0,
            phase="completed",
            phase_label="完成（规则回退）",
            cases=fallback_result["cases"],
            scenarios=fallback_result.get("scenarios", []),
            message=fallback_result.get("message", "规则回退生成完成"),
        )
        return

    if not params.api_key:
        fallback_result = generator._generate_fallback(parsed)
        await _update_progress(
            task_id,
            status="completed",
            progress=1.0,
            phase="completed",
            phase_label="完成（规则回退）",
            cases=fallback_result["cases"],
            scenarios=fallback_result.get("scenarios", []),
            message=fallback_result.get("message", "规则回退生成完成"),
        )
        return

    total_apis = len(parsed["apis"])
    total_batches = (total_apis + BATCH_SIZE - 1) // BATCH_SIZE

    # 根据任务规模自动调整 max_tokens 和 timeout
    effective_params = AIParams(
        api_key=params.api_key,
        base_url=params.base_url,
        model=params.model,
        provider=params.provider,
        timeout=max(params.timeout, 120),
        max_tokens=max(params.max_tokens, 4096),
        temperature=params.temperature,
        group_id=params.group_id,
    )
    _logger.info(
        "AI 生成参数(流水线模式): provider=%s model=%s max_tokens=%d->%d timeout=%d->%d total_apis=%d batches=%d",
        params.provider, params.model,
        params.max_tokens, effective_params.max_tokens,
        params.timeout, effective_params.timeout,
        total_apis, total_batches,
    )

    start_time = time.time()
    all_cases = []
    accumulated_analysis = {
        "resource_groups": [],
        "relationships": [],
        "auth_pattern": {"type": "unknown"},
        "data_flow": [],
    }

    try:
        # ---- 流水线：每批先分析再生成用例 ----
        await _update_progress(
            task_id,
            status="PROGRESS",
            progress=0.02,
            phase="analyzing",
            phase_label=f"正在分析并生成用例 (0/{total_batches} 批次)...",
            total_apis=total_apis,
            processed_apis=0,
            total_batches=total_batches,
            current_batch=0,
            start_time=start_time,
        )

        for batch_idx in range(total_batches):
            # 每批次前检查取消标志
            if task_id:
                if await _check_cancelled(task_id):
                    _logger.info("任务 %s 被用户取消，停止生成，已生成 %d 个用例", task_id, len(all_cases))
                    raise asyncio.CancelledError("任务被用户取消")

                # 每批次重新加载 AI 配置
                reloaded = await _reload_ai_params(task_id)
                if reloaded and reloaded.api_key:
                    effective_params = AIParams(
                        api_key=reloaded.api_key,
                        base_url=reloaded.base_url,
                        model=reloaded.model,
                        provider=reloaded.provider,
                        timeout=max(reloaded.timeout, 120),
                        max_tokens=max(reloaded.max_tokens, 4096),
                        temperature=reloaded.temperature,
                        group_id=reloaded.group_id,
                    )
                    _logger.info("任务 %s 批次 %d 重载 AI 配置: provider=%s model=%s",
                                 task_id, batch_idx + 1, effective_params.provider, effective_params.model)

            start = batch_idx * BATCH_SIZE
            end = min(start + BATCH_SIZE, total_apis)
            batch_apis = parsed["apis"][start:end]

            # 给每个 API 加上全局索引
            batch_with_index = []
            for i, api in enumerate(batch_apis):
                api_copy = dict(api)
                api_copy["_global_index"] = start + i
                batch_with_index.append(api_copy)

            # ---- Step A: 分析当前批次 ----
            await _update_progress(
                task_id,
                status="PROGRESS",
                progress=round(0.02 + 0.88 * batch_idx / total_batches, 3),
                phase="analyzing",
                phase_label=f"正在分析第 {batch_idx + 1}/{total_batches} 批次接口...",
                total_apis=total_apis,
                processed_apis=start,
                total_batches=total_batches,
                current_batch=batch_idx + 1,
                cases=list(all_cases),
                start_time=start_time,
            )

            try:
                batch_analysis = await generator._phase_analyze_batch(
                    batch_with_index, parsed, effective_params, accumulated_analysis
                )
                # 合并到累积分析结果
                accumulated_analysis = generator._merge_analysis(accumulated_analysis, batch_analysis)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _logger.error("批次 %d 分析失败: %s，跳过分析直接生成", batch_idx + 1, e, exc_info=True)
                # 分析失败不阻断，用已有的累积分析继续生成

            # ---- Step B: 为当前批次生成用例 ----
            await _update_progress(
                task_id,
                status="PROGRESS",
                progress=round(0.02 + 0.88 * (batch_idx + 0.5) / total_batches, 3),
                phase="generating_cases",
                phase_label=f"正在生成第 {batch_idx + 1}/{total_batches} 批次用例...",
                total_apis=total_apis,
                processed_apis=start,
                total_batches=total_batches,
                current_batch=batch_idx + 1,
                cases=list(all_cases),
                start_time=start_time,
            )

            prompt = generator._build_case_generation_prompt(
                batch_with_index, parsed, accumulated_analysis, options
            )
            messages = [
                {
                    "role": "system",
                    "content": "你是API测试工程师。只返回JSON，不要其他文字。严格规则：1)每个用例必须有status_code断言(正向range 2xx/3xx,鉴权range 4xx,异常equals具体码) 2)断言field用status_code或$.xxx(JSONPath) 3)提取器用extractorType和variableName(不是type/variable) 4)鉴权用例不带Authorization头",
                },
                {"role": "user", "content": prompt},
            ]

            try:
                result = await _call_llm_with_retry(effective_params, messages, timeout=BATCH_TIMEOUT)
                batch_cases = result.get("cases", [])
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _logger.error("批次 %d AI 生成失败: %s", batch_idx + 1, e, exc_info=True)
                batch_cases = []

            # 补充 base_url 到 url 中
            for case in batch_cases:
                url = case.get("url", "")
                if url and not url.startswith("http"):
                    case["url"] = parsed["base_url"].rstrip("/") + "/" + url.lstrip("/")

            # 累积用例并立即保存到 task_store
            all_cases.extend(batch_cases)

            await _update_progress(
                task_id,
                status="PROGRESS",
                progress=round(0.02 + 0.88 * (batch_idx + 1) / total_batches, 3),
                phase="generating_cases",
                phase_label=f"已生成 {len(all_cases)} 个用例 ({batch_idx + 1}/{total_batches} 批次)",
                total_apis=total_apis,
                processed_apis=end,
                total_batches=total_batches,
                current_batch=batch_idx + 1,
                cases=list(all_cases),
                start_time=start_time,
            )

            _logger.info(
                "流水线批次 %d/%d 完成: 分析+生成，本批 %d 个用例，累计 %d 个",
                batch_idx + 1, total_batches, len(batch_cases), len(all_cases),
            )

        # ---- Phase 3: 生成场景链（所有批次完成后） ----
        include_chain = options.get("include_chain", True)
        scenarios = []
        if include_chain and all_cases:
            await _update_progress(
                task_id,
                status="PROGRESS",
                progress=0.95,
                phase="generating_scenarios",
                phase_label="正在生成测试场景链...",
                total_apis=total_apis,
                processed_apis=total_apis,
                total_batches=total_batches,
                current_batch=total_batches,
                cases=all_cases,
                start_time=start_time,
            )
            scenarios = await generator._phase_generate_scenarios(parsed, accumulated_analysis, all_cases, effective_params)

        # ---- 完成 ----
        elapsed = time.time() - start_time
        await _update_progress(
            task_id,
            status="completed",
            progress=1.0,
            phase="completed",
            phase_label=f"生成完成：{len(all_cases)} 个用例，{len(scenarios)} 个场景",
            total_apis=total_apis,
            processed_apis=total_apis,
            total_batches=total_batches,
            current_batch=total_batches,
            cases=all_cases,
            scenarios=scenarios,
            message=f"AI 生成完成，共 {len(all_cases)} 个用例，{len(scenarios)} 个场景，耗时 {elapsed:.1f}s",
            start_time=start_time,
        )

    except asyncio.CancelledError:
        # 用户主动取消 - 保留已生成的用例（已通过每批保存到 task_store）
        existing_cases = list(all_cases)
        elapsed = time.time() - start_time
        case_count = len(existing_cases)
        await _update_progress(
            task_id,
            status="cancelled",
            progress=round(0.02 + 0.88 * case_count / max(total_apis * 3, 1), 3),
            phase="cancelled",
            phase_label=f"用户已中止，已保留 {case_count} 个用例",
            cases=existing_cases,
            scenarios=[],
            message=f"AI 生成已被用户中止。已保留已生成的 {case_count} 个用例，可在预览页查看并导入。",
            error=None,
            start_time=start_time,
        )
    except RateLimitExceededError as e:
        _logger.error("AI 窗口限额耗尽 task_id=%s: %s", task_id, e)
        existing_cases = list(all_cases)
        if existing_cases:
            elapsed = time.time() - start_time
            await _update_progress(
                task_id,
                status="completed",
                progress=1.0,
                phase="completed",
                phase_label=f"AI 限额耗尽，已保留 {len(existing_cases)} 个用例",
                cases=existing_cases,
                scenarios=[],
                message=f"AI 限额耗尽（{e.provider}），已保留已生成的 {len(existing_cases)} 个用例。可先导入这些用例，等待限额重置后再生成剩余部分。",
                error=None,
                start_time=start_time,
            )
        else:
            fallback_result = generator._generate_fallback(parsed)
            fallback_msg = (
                f"AI API 窗口限额已耗尽（{e.provider}），已自动切换为规则生成模式。"
                f"共生成 {len(fallback_result['cases'])} 个基础用例。"
                f"如需 AI 智能生成，请等待限额重置后重试。"
            )
            await _update_progress(
                task_id,
                status="completed",
                progress=1.0,
                phase="completed",
                phase_label="完成（AI 限额耗尽，已回退规则生成）",
                cases=fallback_result["cases"],
                scenarios=fallback_result.get("scenarios", []),
                message=fallback_msg,
                error=None,
                start_time=start_time,
            )
    except Exception as e:
        _logger.error("AI 生成任务失败 task_id=%s: %s", task_id, e, exc_info=True)
        existing_cases = list(all_cases)
        if existing_cases:
            elapsed = time.time() - start_time
            await _update_progress(
                task_id,
                status="completed",
                progress=1.0,
                phase="completed",
                phase_label=f"生成中断，已保留 {len(existing_cases)} 个用例",
                cases=existing_cases,
                scenarios=[],
                message=f"AI 生成中断，已保留已生成的 {len(existing_cases)} 个用例。错误: {str(e)[:100]}",
                error=None,
                start_time=start_time,
            )
        else:
            try:
                fallback_result = generator._generate_fallback(parsed)
                await _update_progress(
                    task_id,
                    status="completed",
                    progress=1.0,
                    phase="completed",
                    phase_label="完成（AI 失败，已回退规则生成）",
                    cases=fallback_result["cases"],
                    scenarios=fallback_result.get("scenarios", []),
                    message=f"AI 生成失败，已自动切换规则生成。共 {len(fallback_result['cases'])} 个用例。错误: {str(e)[:100]}",
                    error=None,
                    start_time=start_time,
                )
            except Exception:
                await _update_progress(
                    task_id,
                    status="failed",
                    progress=0,
                    phase="failed",
                    phase_label="生成失败",
                    error=str(e),
                    message=f"生成失败: {str(e)[:200]}",
                    start_time=start_time,
                )


# ======================================================================
# Celery 任务定义
# ======================================================================

from fastapi_backend.celery_config import app as _celery_app


@_celery_app.task(bind=True, name="fastapi_backend.services.autotest_ai_generator.ai_generate_task", time_limit=600)
def ai_generate_task(self, task_id: str, swagger_data: dict, options: dict):
    """Celery 任务：AI 生成测试用例"""
    try:
        asyncio.run(_run_generation(task_id, swagger_data, options))
    except Exception as e:
        _logger.error("Celery AI 生成任务异常 task_id=%s: %s", task_id, e, exc_info=True)
        # 确保任务状态更新为失败
        try:
            from fastapi_backend.services.autotest_task_store import update_task, get_task
            stored = get_task(task_id) or {"task_id": task_id}
            stored.update({
                "status": "failed",
                "error": str(e),
                "message": f"生成失败: {str(e)[:200]}",
            })
            import asyncio as _aio
            _aio.run(update_task(task_id, stored))
        except Exception:
            pass
