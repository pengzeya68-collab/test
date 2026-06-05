"""
Mock 服务引擎

功能：
- Mock 规则匹配（支持条件响应）
- Mock 响应生成
- 请求日志记录
- 从 Swagger 导入规则
"""

import asyncio
import fnmatch
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.models.autotest import MockProject, MockRule, MockRequestLog

_logger = logging.getLogger(__name__)


class MockEngine:
    """Mock 服务引擎"""

    async def match_rule(
        self, db: AsyncSession, project_slug: str, method: str, path: str, request_params: dict = None
    ) -> Optional[MockRule]:
        """
        按优先级匹配 Mock 规则。
        支持精确匹配和通配符匹配。
        """
        # 查找项目
        result = await db.execute(
            select(MockProject).where(MockProject.base_url_slug == project_slug, MockProject.is_active == True)
        )
        project = result.scalar_one_or_none()
        if not project:
            return None

        # 获取所有启用的规则，按优先级降序
        result = await db.execute(
            select(MockRule)
            .where(MockRule.project_id == project.id, MockRule.is_active == True)
            .order_by(MockRule.priority.desc())
        )
        rules = result.scalars().all()

        for rule in rules:
            if rule.method.upper() != method.upper():
                continue

            # 路径匹配：支持精确匹配和通配符
            if self._match_path(rule.path, path):
                # 条件匹配
                if rule.condition:
                    if not self._evaluate_condition(rule.condition, request_params or {}):
                        continue
                return rule

        return None

    def _match_path(self, pattern: str, path: str) -> bool:
        """路径匹配，支持通配符 * 和 ?"""
        # 精确匹配
        if pattern == path:
            return True
        # 通配符匹配
        if fnmatch.fnmatch(path, pattern):
            return True
        # 去掉前导斜杠再匹配
        if fnmatch.fnmatch(path.lstrip("/"), pattern.lstrip("/")):
            return True
        return False

    def _evaluate_condition(self, condition: dict, request_params: dict) -> bool:
        """
        评估条件响应规则。
        condition 格式: {"param": "name", "operator": "eq", "value": "test"}
        支持从 query/body/header 中取值
        """
        if not condition or not isinstance(condition, dict):
            return True

        param_name = condition.get("param", "")
        operator = condition.get("operator", "eq")
        expected = condition.get("value", "")
        source = condition.get("source", "query")  # query / body / header

        # 根据 source 从对应子字典中取值
        source_map = request_params.get(source, request_params) if isinstance(request_params, dict) else request_params
        actual = source_map.get(param_name) if isinstance(source_map, dict) else request_params.get(param_name)

        try:
            if operator in ("eq", "equals", "=="):
                return str(actual) == str(expected)
            elif operator in ("ne", "not_equals", "!="):
                return str(actual) != str(expected)
            elif operator == "contains":
                return str(expected) in str(actual) if actual else False
            elif operator in ("gt", ">"):
                return float(actual) > float(expected)
            elif operator in ("lt", "<"):
                return float(actual) < float(expected)
            elif operator == "exists":
                return actual is not None
            elif operator == "not_exists":
                return actual is None
            elif operator == "regex":
                return bool(re.search(str(expected), str(actual))) if actual else False
        except Exception:
            return False

        return False

    async def generate_response(self, rule: MockRule) -> Dict[str, Any]:
        """根据规则生成响应，支持延迟"""
        if rule.delay_ms and rule.delay_ms > 0:
            await asyncio.sleep(rule.delay_ms / 1000.0)

        headers = rule.response_headers or {}
        if "Content-Type" not in headers and "content-type" not in headers:
            headers["Content-Type"] = "application/json"

        body = rule.response_body
        if body is None:
            body = {"message": "ok"}

        return {
            "status": rule.response_status,
            "headers": headers,
            "body": body,
        }

    async def log_request(
        self,
        db: AsyncSession,
        project_id: int,
        rule_id: Optional[int],
        method: str,
        path: str,
        request_headers: dict,
        request_body: str,
        response_status: int,
        response_body: str,
        response_time_ms: int,
        matched_rule_name: Optional[str] = None,
    ):
        """记录 Mock 请求日志"""
        log = MockRequestLog(
            project_id=project_id,
            rule_id=rule_id,
            method=method,
            path=path,
            request_headers=request_headers,
            request_body=request_body,
            response_status=response_status,
            response_body=response_body[:5000] if response_body else None,
            response_time_ms=response_time_ms,
            matched_rule_name=matched_rule_name,
        )
        db.add(log)
        await db.commit()

    async def import_from_swagger(self, db: AsyncSession, project_id: int, swagger_data: dict) -> int:
        """
        从 Swagger/OpenAPI 文档导入 Mock 规则。
        返回创建的规则数。
        """
        paths = swagger_data.get("paths", {})
        created_count = 0

        for path, methods in paths.items():
            for method, spec in methods.items():
                if method.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    continue

                # 从 responses 中提取 200 响应
                responses = spec.get("responses", {})
                ok_response = responses.get("200", responses.get("201", {}))

                # 尝试从 schema 生成 mock 数据
                response_body = self._generate_mock_from_schema(ok_response)

                rule = MockRule(
                    project_id=project_id,
                    method=method.upper(),
                    path=path,
                    name=spec.get("summary", f"{method.upper()} {path}"),
                    description=spec.get("description", ""),
                    response_status=200,
                    response_body=response_body,
                )
                db.add(rule)
                created_count += 1

        await db.commit()
        return created_count

    def _generate_mock_from_schema(self, response_spec: dict) -> dict:
        """从 OpenAPI schema 生成 mock 数据"""
        schema = response_spec.get("schema", response_spec.get("content", {}).get("application/json", {}).get("schema", {}))
        if not schema:
            return {"message": "ok"}
        return self._mock_value(schema)

    def _mock_value(self, schema: dict) -> Any:
        """递归生成 mock 数据"""
        if not isinstance(schema, dict):
            return schema

        schema_type = schema.get("type", "object")

        if "example" in schema:
            return schema["example"]
        elif "enum" in schema:
            return schema["enum"][0]
        elif schema_type == "string":
            fmt = schema.get("format", "")
            if fmt == "email":
                return "test@example.com"
            elif fmt == "date-time":
                return "2024-01-01T00:00:00Z"
            elif fmt == "date":
                return "2024-01-01"
            elif fmt == "uuid":
                return str(uuid.uuid4())
            return "string"
        elif schema_type in ("integer", "number"):
            return schema.get("minimum", 0)
        elif schema_type == "boolean":
            return True
        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._mock_value(items)]
        elif schema_type == "object":
            properties = schema.get("properties", {})
            result = {}
            for prop_name, prop_schema in properties.items():
                result[prop_name] = self._mock_value(prop_schema)
            return result

        return {}


# 全局引擎实例
mock_engine = MockEngine()
