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
import random
import re
import string
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

    _faker_instance = None  # 缓存 Faker 实例，避免每次请求重新加载 zh_CN 语言包

    @classmethod
    def _get_faker(cls):
        """获取或创建 Faker 单例"""
        if cls._faker_instance is None:
            try:
                from faker import Faker
                cls._faker_instance = Faker('zh_CN')
            except ImportError:
                cls._faker_instance = False  # 标记为不可用
        return cls._faker_instance if cls._faker_instance is not False else None

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

        # 解析响应体中的 @表达式 动态值
        body = self._resolve_dynamic_values(body)

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
        await db.flush()

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
        """递归生成 mock 数据（增强版：复用 DataFactory 生成模式）"""
        if not isinstance(schema, dict):
            return schema

        schema_type = schema.get("type", "object")

        if "example" in schema:
            return schema["example"]
        elif "enum" in schema:
            return schema["enum"][0]
        elif schema_type == "string":
            fmt = schema.get("format", "")
            # 检查 x-mock-expression 动态表达式
            mock_expr = schema.get("x-mock-expression", "")
            if mock_expr:
                return self._resolve_expression(mock_expr)
            if fmt == "email":
                return self._gen_email()
            elif fmt in ("phone", "tel"):
                return self._gen_phone()
            elif fmt == "date-time":
                return datetime.now(timezone.utc).isoformat()
            elif fmt == "date":
                return datetime.now(timezone.utc).strftime("%Y-%m-%d")
            elif fmt == "uuid":
                return str(uuid.uuid4())
            return "string"
        elif schema_type in ("integer", "number"):
            minimum = schema.get("minimum", 0)
            maximum = schema.get("maximum", 1000)
            if schema_type == "integer":
                return random.randint(int(minimum), int(maximum))
            return round(random.uniform(float(minimum), float(maximum)), 2)
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

    # ========== 动态值生成（复用 DataFactory 模式） ==========

    def _gen_phone(self) -> str:
        """生成随机手机号（复用 DataFactory 前缀列表）"""
        prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                     "150", "151", "152", "153", "155", "156", "157", "158", "159",
                     "180", "181", "182", "183", "184", "185", "186", "187", "188", "189"]
        return random.choice(prefixes) + ''.join(random.choices(string.digits, k=8))

    def _gen_email(self) -> str:
        """生成随机邮箱"""
        return f"testuser{random.randint(1000, 9999)}@test.com"

    def _gen_uuid(self) -> str:
        return str(uuid.uuid4())

    def _gen_timestamp(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _gen_datetime(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _resolve_expression(self, expr: str) -> Any:
        """解析 @表达式 为动态值"""
        if not expr or not isinstance(expr, str):
            return expr
        expr = expr.strip()
        if not expr.startswith("@"):
            return expr

        name = expr[1:].lower()

        # 带参数的表达式: @integer(1,100)
        param_match = re.match(r'^(\w+)\(([^)]*)\)$', name)
        if param_match:
            func_name = param_match.group(1)
            args_str = param_match.group(2)
            if func_name == 'integer':
                try:
                    parts = [int(x.strip()) for x in args_str.split(',')]
                    lo, hi = parts[0], parts[1] if len(parts) > 1 else parts[0]
                    return random.randint(lo, hi)
                except (ValueError, IndexError):
                    return random.randint(0, 100)
            elif func_name == 'float':
                try:
                    parts = [float(x.strip()) for x in args_str.split(',')]
                    lo, hi = parts[0], parts[1] if len(parts) > 1 else parts[0]
                    return round(random.uniform(lo, hi), 2)
                except (ValueError, IndexError):
                    return round(random.uniform(0, 100), 2)
            elif func_name == 'string':
                try:
                    length = int(args_str.strip())
                    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
                except (ValueError, IndexError):
                    return ''.join(random.choices(string.ascii_letters, k=8))

        # 基础表达式
        generators = {
            "phone": self._gen_phone,
            "email": self._gen_email,
            "uuid": self._gen_uuid,
            "timestamp": self._gen_timestamp,
            "datetime": self._gen_datetime,
        }
        if name in generators:
            return generators[name]()

        # faker 表达式（name, address, id_card 等）
        try:
            return self._faker_generate(name)
        except Exception:
            return expr

    def _faker_generate(self, name: str) -> str:
        """使用 faker 生成中文数据"""
        fake = self._get_faker()
        if fake is None:
            # faker 未安装时回退到简单随机
            fallback = {
                "name": lambda: f"用户{random.randint(1000, 9999)}",
                "address": f"北京市某某路{random.randint(1, 999)}号",
                "id_card": f"1101011990010{random.randint(10000, 99999)}",
                "company": f"测试公司{random.randint(1, 100)}",
                "sentence": "这是一条测试句子。",
                "paragraph": "这是一段测试文本，用于生成 mock 数据。",
                "word": "测试",
                "text": "测试文本内容",
                "job": "工程师",
            }
            gen_fn = fallback.get(name)
            if gen_fn:
                return gen_fn()
            raise ValueError(f"faker 未安装且无回退数据: @{name}")

        faker_map = {
            "name": fake.name,
            "address": fake.address,
            "id_card": fake.ssn,
            "company": fake.company,
            "sentence": lambda: fake.sentence(nb_words=6),
            "paragraph": lambda: fake.paragraph(nb_sentences=3),
            "word": fake.word,
            "text": lambda: fake.text(max_nb_chars=200),
            "job": fake.job,
            "phone_number": fake.phone_number,
            "zipcode": fake.postcode,
            "city": fake.city,
            "province": fake.province,
            "country": fake.country,
            "url": fake.url,
            "ipv4": fake.ipv4,
            "color": fake.color_name,
        }
        gen_fn = faker_map.get(name)
        if gen_fn:
            return gen_fn()
        raise ValueError(f"未知的 faker 表达式: @{name}")

    def _resolve_dynamic_values(self, body: Any) -> Any:
        """递归替换响应体中的 @表达式"""
        if isinstance(body, str):
            if body.startswith("@") and len(body) < 50:
                return self._resolve_expression(body)
            return body
        elif isinstance(body, dict):
            return {k: self._resolve_dynamic_values(v) for k, v in body.items()}
        elif isinstance(body, list):
            return [self._resolve_dynamic_values(item) for item in body]
        return body


# 全局引擎实例
mock_engine = MockEngine()
