"""
API 文档生成服务

从 AutoTestCase 用例数据自动生成 API 文档，支持三种格式：
- OpenAPI 3.0 规范（JSON）
- Markdown 文档
- 独立 HTML 文档（内联 CSS/JS，可离线查看）

设计目标：对标 Apifox 自动 API 文档，"文档即用例"。
"""

import html
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup


# ========== 工具函数 ==========


def _guess_type(value: Any) -> str:
    """根据 Python 值推断 JSON Schema 类型"""
    if value is None:
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def _json_to_schema(value: Any) -> Dict[str, Any]:
    """将任意 JSON 值递归转换为 JSON Schema（用于请求体/响应示例）"""
    if isinstance(value, dict):
        props = {}
        for k, v in value.items():
            props[k] = _json_to_schema(v)
        return {"type": "object", "properties": props}
    if isinstance(value, list):
        if value:
            return {"type": "array", "items": _json_to_schema(value[0])}
        return {"type": "array", "items": {}}
    return {"type": _guess_type(value), "example": value}


def _normalize_path(url: str) -> str:
    """从完整 URL 或相对路径中提取 OpenAPI path 部分

    例：
      "https://api.example.com/v1/users/1" -> "/v1/users/1"
      "/api/login" -> "/api/login"
      "api/login" -> "/api/login"
    """
    if not url:
        return "/"
    parsed = urlparse(url)
    path = parsed.path
    if not path:
        # 无 scheme 的相对路径
        path = url if url.startswith("/") else "/" + url
    if not path.startswith("/"):
        path = "/" + path
    return path or "/"


def _safe_operation_id(method: str, path: str, idx: int) -> str:
    """生成唯一的 operationId"""
    cleaned = path.replace("/", "_").replace("{", "").replace("}", "").strip("_")
    cleaned = cleaned or "root"
    return f"{method.lower()}_{cleaned}_{idx}"


def _md_escape_cell(text: Any) -> str:
    """转义 Markdown 表格单元格内容：转义 | 和反斜杠，替换换行为空格"""
    s = str(text) if text is not None else ""
    s = s.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    return s


def _md_escape_inline(text: Any) -> str:
    """转义 Markdown 行内文本中的 HTML 特殊字符与中括号，防止 XSS 与链接语法破坏"""
    s = str(text) if text is not None else ""
    s = html.escape(s, quote=False)
    s = s.replace("[", "\\[").replace("]", "\\]")
    return s


# 允许的 HTTP 方法白名单（用于 HTML 文档方法徽标，防止 XSS）
_ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}


def _sanitize_method(method: Any) -> str:
    """对 HTTP 方法做白名单校验，返回安全的大写方法名

    非白名单值统一返回 "GET"，避免将用户可控的 method 字段直接拼入 HTML 导致 XSS。
    """
    if not method:
        return "GET"
    m = str(method).upper().strip()
    return m if m in _ALLOWED_METHODS else "GET"


# ========== 主服务类 ==========


class ApiDocGenerator:
    """API 文档生成器：从用例生成 OpenAPI / Markdown / HTML 文档"""

    @staticmethod
    async def _fetch_cases(
        db: AsyncSession,
        case_ids: Optional[List[int]] = None,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        owner_user_id: Optional[int] = None,
    ) -> Tuple[List[AutoTestCase], Dict[int, str]]:
        """查询用例列表及分组名映射

        - user_id 不为 None 时按用户过滤（用于登录态生成文档）
        - user_id 为 None 时不按用户过滤（用于分享文档公开访问，case_ids 已在分享时校验归属）
        - owner_user_id 用于公开访问时对 group_map 做归属过滤，避免泄露其他用户分组名
        - case_ids 优先于 group_id
        返回 (cases, group_map)
        """
        # 安全防护：公开访问（user_id=None）时必须有 case_ids 或 group_id 过滤，
        # 否则会泄露所有用户的用例数据
        if user_id is None and not case_ids and group_id is None:
            return [], {}

        query = select(AutoTestCase)
        if user_id is not None:
            query = query.where(AutoTestCase.user_id == user_id)
        if case_ids:
            query = query.where(AutoTestCase.id.in_(case_ids))
        elif group_id is not None:
            query = query.where(AutoTestCase.group_id == group_id)

        query = query.order_by(AutoTestCase.id)
        result = await db.execute(query)
        cases = list(result.scalars().all())

        # 批量获取分组名，避免 N+1 查询
        group_ids = list({c.group_id for c in cases if c.group_id is not None})
        group_map: Dict[int, str] = {}
        if group_ids:
            g_query = select(AutoTestGroup).where(AutoTestGroup.id.in_(group_ids))
            # 登录态：按当前用户过滤；公开访问：按分享归属者过滤，防止泄露其他用户分组名
            if user_id is not None:
                g_query = g_query.where(AutoTestGroup.user_id == user_id)
            elif owner_user_id is not None:
                g_query = g_query.where(AutoTestGroup.user_id == owner_user_id)
            g_result = await db.execute(g_query)
            for g in g_result.scalars().all():
                group_map[g.id] = g.name
        return cases, group_map

    @staticmethod
    async def generate_doc(
        db: AsyncSession,
        case_ids: Optional[List[int]] = None,
        group_id: Optional[int] = None,
        format: str = "openapi",
        user_id: Optional[int] = None,
        title: str = "TestMaster API 文档",
        owner_user_id: Optional[int] = None,
    ) -> Any:
        """从用例生成 API 文档（统一入口）

        :param format: openapi | markdown | html
        :param owner_user_id: 公开访问时用于 group_map 归属过滤
        :return: openapi 返回 dict，markdown/html 返回 str
        """
        fmt = (format or "openapi").lower()
        if fmt == "openapi":
            return await ApiDocGenerator.generate_openapi_spec(
                db, case_ids, group_id, user_id=user_id, title=title, owner_user_id=owner_user_id
            )
        if fmt == "markdown":
            return await ApiDocGenerator.generate_markdown(
                db, case_ids, group_id, user_id=user_id, title=title, owner_user_id=owner_user_id
            )
        if fmt == "html":
            return await ApiDocGenerator.generate_html(
                db, case_ids, group_id, user_id=user_id, title=title, owner_user_id=owner_user_id
            )
        raise ValueError(f"不支持的文档格式: {format}，仅支持 openapi/markdown/html")

    # ---------- OpenAPI 3.0 ----------

    @staticmethod
    async def generate_openapi_spec(
        db: AsyncSession,
        case_ids: Optional[List[int]] = None,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        title: str = "TestMaster API 文档",
        owner_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """生成 OpenAPI 3.0 规范"""
        cases, group_map = await ApiDocGenerator._fetch_cases(
            db, case_ids, group_id, user_id, owner_user_id=owner_user_id
        )

        paths: Dict[str, Dict[str, Any]] = {}
        tags_order: List[str] = []
        tags_seen = set()
        # 收集同名 response_schema 以复用为 components.schemas
        components_schemas: Dict[str, Dict[str, Any]] = {}
        # 是否检测到 Bearer 鉴权
        has_bearer_security = False

        for idx, case in enumerate(cases):
            path_item = ApiDocGenerator._case_to_openapi_path(case, group_map, idx)
            path = path_item["path"]
            method = path_item["method"]
            operation = path_item["operation"]

            # 检测 Authorization header 是否使用 Bearer
            headers = case.headers
            if isinstance(headers, dict):
                for k, v in headers.items():
                    if str(k).lower() == "authorization" and isinstance(v, str) and v.lower().startswith("bearer "):
                        has_bearer_security = True
                        break

            # 收集可复用 schema（仅当 response_schema 带 title 字段时提取）
            response_schema = case.response_schema
            if isinstance(response_schema, dict) and response_schema.get("title"):
                schema_name = str(response_schema["title"])
                if schema_name not in components_schemas:
                    components_schemas[schema_name] = response_schema

            if path not in paths:
                paths[path] = {}

            if method in paths[path]:
                # D6: 同一 path + method 多版本不再覆盖，追加到 x-testmaster-cases 数组
                existing = paths[path][method]
                cases_list = existing.setdefault("x-testmaster-cases", [])
                cases_list.append(
                    {
                        "id": case.id,
                        "name": case.name or path,
                        "summary": case.description or "",
                    }
                )
            else:
                # 首个用例写入 operation，并初始化 x-testmaster-cases
                operation["x-testmaster-cases"] = [
                    {
                        "id": case.id,
                        "name": case.name or path,
                        "summary": case.description or "",
                    }
                ]
                paths[path][method] = operation

            tag = operation.get("tags", ["default"])[0]
            if tag not in tags_seen:
                tags_seen.add(tag)
                tags_order.append(tag)

        spec: Dict[str, Any] = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": "1.0.0",
                "description": "由 TestMaster 用例自动生成的 API 文档（文档即用例）",
            },
            "tags": [{"name": t} for t in tags_order],
            "paths": paths,
        }

        # servers：从环境配置取 baseURL，便于工具直接发起请求
        try:
            from fastapi_backend.core.config import settings

            base_url = getattr(settings, "AUTO_TEST_BASE_URL", None)
            if base_url:
                spec["servers"] = [{"url": base_url, "description": "TestMaster 测试服务基址"}]
        except Exception:
            pass

        # components.schemas：提取同名 response_schema 复用
        if components_schemas:
            spec["components"] = {"schemas": components_schemas}

        # security：若检测到 Bearer 鉴权则声明 BearerAuth 方案
        if has_bearer_security:
            spec.setdefault("components", {})["securitySchemes"] = {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
            spec["security"] = [{"BearerAuth": []}]

        return spec

    @staticmethod
    def _case_to_openapi_path(case: AutoTestCase, group_map: Dict[int, str], idx: int) -> Dict[str, Any]:
        """将单个用例转换为 OpenAPI path item

        返回 {"path": str, "method": str, "operation": dict}
        """
        method = (case.method or "GET").lower()
        path = _normalize_path(case.url or "/")
        group_name = group_map.get(case.group_id, "default") if case.group_id else "default"

        # 构建参数列表（headers + query params）
        parameters: List[Dict[str, Any]] = []
        params = case.params
        if isinstance(params, dict):
            for k, v in params.items():
                parameters.append(
                    {
                        "name": str(k),
                        "in": "query",
                        "required": False,
                        "schema": {"type": _guess_type(v)},
                        "example": v,
                    }
                )

        headers = case.headers
        if isinstance(headers, dict):
            for k, v in headers.items():
                if str(k).lower() in ("content-type", "authorization"):
                    continue
                parameters.append(
                    {
                        "name": str(k),
                        "in": "header",
                        "required": False,
                        "schema": {"type": "string"},
                        "example": v,
                    }
                )

        # 构建请求体
        request_body: Optional[Dict[str, Any]] = None
        body_type = (case.body_type or "none").lower()
        payload = case.payload
        if method in ("post", "put", "patch") and payload is not None and body_type != "none":
            content_type = case.content_type or "application/json"
            if body_type == "form-data":
                content_type = "application/x-www-form-urlencoded"
            elif body_type == "multipart":
                content_type = "multipart/form-data"
            elif body_type in ("xml", "raw_xml"):
                content_type = "application/xml"

            schema = (
                _json_to_schema(payload)
                if isinstance(payload, (dict, list))
                else {"type": "string", "example": payload}
            )
            request_body = {
                "required": bool(payload),
                "content": {content_type: {"schema": schema, "example": payload}},
            }

        # 构建响应（优先使用 response_schema，否则给默认示例）
        response_schema = case.response_schema
        if isinstance(response_schema, dict) and response_schema:
            responses = {
                "200": {
                    "description": "请求成功",
                    "content": {"application/json": {"schema": response_schema}},
                }
            }
        else:
            responses = {
                "200": {
                    "description": "请求成功",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"},
                            "example": {"code": 0, "message": "success", "data": {}},
                        }
                    },
                }
            }

        operation: Dict[str, Any] = {
            "summary": case.name or path,
            "description": case.description or "",
            "operationId": _safe_operation_id(method, path, idx),
            "tags": [group_name],
            "responses": responses,
        }
        if parameters:
            operation["parameters"] = parameters
        if request_body:
            operation["requestBody"] = request_body

        return {"path": path, "method": method, "operation": operation}

    # ---------- Markdown ----------

    @staticmethod
    async def generate_markdown(
        db: AsyncSession,
        case_ids: Optional[List[int]] = None,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        title: str = "TestMaster API 文档",
        owner_user_id: Optional[int] = None,
    ) -> str:
        """生成 Markdown 格式文档（按分组组织）"""
        cases, group_map = await ApiDocGenerator._fetch_cases(
            db, case_ids, group_id, user_id, owner_user_id=owner_user_id
        )

        lines: List[str] = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(
            f"> 由 TestMaster 自动生成 · 共 {len(cases)} 个接口 · 生成时间 {datetime.now(timezone.utc).isoformat()}"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        if not cases:
            lines.append("_暂无用例数据_")
            return "\n".join(lines)

        # 按分组组织
        grouped: Dict[str, List[AutoTestCase]] = {}
        order: List[str] = []
        for c in cases:
            gname = group_map.get(c.group_id, "默认分组") if c.group_id else "默认分组"
            if gname not in grouped:
                grouped[gname] = []
                order.append(gname)
            grouped[gname].append(c)

        # 目录
        lines.append("## 目录")
        lines.append("")
        for gname in order:
            lines.append(f"- **{_md_escape_inline(gname)}**")
            for c in grouped[gname]:
                anchor = f"{_sanitize_method(c.method).lower()}-{c.id}"
                link_text = _md_escape_inline(f"{_sanitize_method(c.method)} {c.name or c.url}")
                lines.append(f"  - [{link_text}](#{anchor})")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 详情
        for gname in order:
            lines.append(f"## {_md_escape_inline(gname)}")
            lines.append("")
            for c in grouped[gname]:
                lines.extend(ApiDocGenerator._case_to_markdown(c))
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _case_to_markdown(case: AutoTestCase) -> List[str]:
        """单个用例转 Markdown 片段"""
        method = _sanitize_method(case.method)
        url = case.url or "/"
        path = _normalize_path(url)
        anchor = f"{method.lower()}-{case.id}"
        lines: List[str] = []
        # D10: 使用 Markdown 标题语法生成锚点，GitHub/VSCode 等渲染器会自动
        # 依据标题文本生成锚点 `method-id`，与目录链接一致，避免 <a id> 标签
        # 在部分渲染器中无法生成锚点的问题。
        lines.append(f'### {_md_escape_inline(case.name or path)} <a id="{anchor}"></a>')
        lines.append("")
        if case.description:
            # D5: description 转义后再拼接，防止 XSS 与 Markdown 语法破坏
            lines.append(_md_escape_inline(case.description))
            lines.append("")

        lines.append(f"- **请求方法**: `{method}`")
        lines.append(f"- **请求路径**: `{path}`")
        lines.append(f"- **完整 URL**: `{url}`")
        lines.append("")

        # 请求头表格
        headers = case.headers
        if isinstance(headers, dict) and headers:
            lines.append("#### 请求头")
            lines.append("")
            lines.append("| 名称 | 示例值 |")
            lines.append("| --- | --- |")
            for k, v in headers.items():
                lines.append(f"| {_md_escape_cell(k)} | `{_md_escape_cell(v)}` |")
            lines.append("")

        # 查询参数表格
        params = case.params
        if isinstance(params, dict) and params:
            lines.append("#### Query 参数")
            lines.append("")
            lines.append("| 名称 | 类型 | 示例值 |")
            lines.append("| --- | --- | --- |")
            for k, v in params.items():
                lines.append(f"| {_md_escape_cell(k)} | {_guess_type(v)} | `{_md_escape_cell(v)}` |")
            lines.append("")

        # 请求体
        body_type = (case.body_type or "none").lower()
        payload = case.payload
        if body_type != "none" and payload is not None:
            content_type = case.content_type or "application/json"
            lines.append("#### 请求体")
            lines.append("")
            lines.append(f"`Content-Type: {content_type}`")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")

        # 响应示例
        response_schema = case.response_schema
        lines.append("#### 响应示例")
        lines.append("")
        if isinstance(response_schema, dict) and response_schema:
            lines.append("**响应 Schema:**")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(response_schema, ensure_ascii=False, indent=2))
            lines.append("```")
        else:
            lines.append("```json")
            lines.append(json.dumps({"code": 0, "message": "success", "data": {}}, ensure_ascii=False, indent=2))
            lines.append("```")
        lines.append("")
        lines.append("---")
        return lines

    # ---------- HTML ----------

    @staticmethod
    async def generate_html(
        db: AsyncSession,
        case_ids: Optional[List[int]] = None,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        title: str = "TestMaster API 文档",
        owner_user_id: Optional[int] = None,
    ) -> str:
        """生成独立 HTML 文档（内联 CSS/JS，可离线查看，类似 Swagger UI）"""
        cases, group_map = await ApiDocGenerator._fetch_cases(
            db, case_ids, group_id, user_id, owner_user_id=owner_user_id
        )

        # 按分组组织
        grouped: Dict[str, List[AutoTestCase]] = {}
        order: List[str] = []
        for c in cases:
            gname = group_map.get(c.group_id, "默认分组") if c.group_id else "默认分组"
            if gname not in grouped:
                grouped[gname] = []
                order.append(gname)
            grouped[gname].append(c)

        # 构建侧边栏 HTML
        sidebar_items: List[str] = []
        for gi, gname in enumerate(order):
            g_id = f"group-{gi}"
            sidebar_items.append(
                f'<div class="nav-group"><div class="nav-group-title" onclick="toggleGroup(\'{g_id}\')">'
                f'<span class="arrow">▼</span> {html.escape(gname)} '
                f'<span class="count">({len(grouped[gname])})</span></div>'
                f'<ul class="nav-list" id="{g_id}">'
            )
            for ci, c in enumerate(grouped[gname]):
                # D3: method 做白名单校验，防止 XSS
                method = _sanitize_method(c.method)
                item_id = f"api-{gi}-{ci}"
                summary = html.escape(c.name or _normalize_path(c.url or "/"))
                sidebar_items.append(
                    f'<li class="nav-item method-{method.lower()}" onclick="selectApi(\'{item_id}\')">'
                    f'<span class="m-badge m-{method.lower()}">{method}</span>'
                    f'<span class="nav-label">{summary}</span></li>'
                )
            sidebar_items.append("</ul></div>")

        # 构建详情 HTML
        detail_items: List[str] = []
        for gi, gname in enumerate(order):
            for ci, c in enumerate(grouped[gname]):
                item_id = f"api-{gi}-{ci}"
                detail_items.append(ApiDocGenerator._case_to_html(c, gname, item_id))

        no_data = ""
        if not cases:
            no_data = '<div class="empty">暂无用例数据</div>'

        gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        sidebar_html = "\n".join(sidebar_items) if sidebar_items else '<div class="empty">无接口</div>'
        detail_html = "\n".join(detail_items)

        return ApiDocGenerator._html_template(
            title=title,
            total=len(cases),
            gen_time=gen_time,
            sidebar=sidebar_html,
            details=detail_html,
            no_data=no_data,
        )

    @staticmethod
    def _case_to_html(case: AutoTestCase, group_name: str, item_id: str) -> str:
        """单个用例转 HTML 详情块"""
        # D3: method 做白名单校验，防止用户可控字段注入 HTML 导致 XSS
        method = _sanitize_method(case.method)
        url = case.url or "/"
        path = _normalize_path(url)
        name = html.escape(case.name or path)
        desc = html.escape(case.description or "") if case.description else ""
        method_lower = method.lower()

        parts: List[str] = [f'<div class="api-block" id="{item_id}">']
        parts.append(
            f'<div class="api-head"><span class="m-badge m-{method_lower}">{method}</span>'
            f'<h3 class="api-title">{name}</h3></div>'
        )
        if desc:
            parts.append(f'<p class="api-desc">{desc}</p>')
        parts.append(
            f'<div class="api-url"><span class="m-badge m-{method_lower}">{method}</span>'
            f'<code class="url-text">{html.escape(path)}</code></div>'
        )
        parts.append(
            f'<div class="api-meta">分组: <b>{html.escape(group_name)}</b> · 完整 URL: <code>{html.escape(url)}</code></div>'
        )

        # 请求头
        headers = case.headers
        if isinstance(headers, dict) and headers:
            rows = "".join(
                f"<tr><td>{html.escape(str(k))}</td><td><code>{html.escape(str(v))}</code></td></tr>"
                for k, v in headers.items()
            )
            parts.append(
                f'<div class="section"><h4>请求头</h4><table class="tbl"><tr><th>名称</th><th>示例值</th></tr>{rows}</table></div>'
            )

        # 查询参数
        params = case.params
        if isinstance(params, dict) and params:
            rows = "".join(
                f"<tr><td>{html.escape(str(k))}</td><td>{_guess_type(v)}</td><td><code>{html.escape(str(v))}</code></td></tr>"
                for k, v in params.items()
            )
            parts.append(
                f'<div class="section"><h4>Query 参数</h4><table class="tbl"><tr><th>名称</th><th>类型</th><th>示例值</th></tr>{rows}</table></div>'
            )

        # 请求体
        body_type = (case.body_type or "none").lower()
        payload = case.payload
        if body_type != "none" and payload is not None:
            content_type = case.content_type or "application/json"
            body_str = json.dumps(payload, ensure_ascii=False, indent=2)
            parts.append(
                f'<div class="section"><h4>请求体 <span class="ct">({html.escape(content_type)})</span></h4>'
                f'<pre class="code">{html.escape(body_str)}</pre></div>'
            )

        # 响应
        response_schema = case.response_schema
        if isinstance(response_schema, dict) and response_schema:
            resp_str = json.dumps(response_schema, ensure_ascii=False, indent=2)
            parts.append(
                f'<div class="section"><h4>响应 Schema</h4><pre class="code">{html.escape(resp_str)}</pre></div>'
            )
        else:
            default_resp = json.dumps({"code": 0, "message": "success", "data": {}}, ensure_ascii=False, indent=2)
            parts.append(
                f'<div class="section"><h4>响应示例（默认）</h4><pre class="code">{html.escape(default_resp)}</pre></div>'
            )

        parts.append("</div>")
        return "".join(parts)

    @staticmethod
    def _html_template(title: str, total: int, gen_time: str, sidebar: str, details: str, no_data: str) -> str:
        """完整 HTML 模板（内联 CSS + JS，支持分组折叠与搜索）"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f7fa; color: #303133; }}
  .layout {{ display: flex; min-height: 100vh; }}
  /* 侧边栏 */
  .sidebar {{ width: 280px; background: #fff; border-right: 1px solid #e4e7ed; position: fixed; top: 0; bottom: 0; left: 0; display: flex; flex-direction: column; }}
  .sidebar-header {{ padding: 16px; border-bottom: 1px solid #ebeef5; }}
  .sidebar-header h1 {{ font-size: 18px; color: #303133; margin-bottom: 8px; }}
  .search-box {{ width: 100%; padding: 8px 12px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 13px; outline: none; }}
  .search-box:focus {{ border-color: #409eff; }}
  .stats {{ padding: 8px 16px; font-size: 12px; color: #909399; border-bottom: 1px solid #ebeef5; }}
  .nav {{ flex: 1; overflow-y: auto; padding: 8px; }}
  .nav-group {{ margin-bottom: 4px; }}
  .nav-group-title {{ padding: 8px 10px; cursor: pointer; font-weight: 500; font-size: 13px; color: #303133; border-radius: 4px; user-select: none; }}
  .nav-group-title:hover {{ background: #f5f7fa; }}
  .nav-group-title .arrow {{ display: inline-block; width: 12px; font-size: 10px; color: #909399; transition: transform .2s; }}
  .nav-group.collapsed .arrow {{ transform: rotate(-90deg); }}
  .nav-group.collapsed .nav-list {{ display: none; }}
  .nav-list {{ list-style: none; padding: 2px 0; }}
  .nav-item {{ padding: 6px 10px 6px 24px; cursor: pointer; font-size: 13px; color: #606266; border-radius: 4px; display: flex; align-items: center; gap: 8px; }}
  .nav-item:hover {{ background: #ecf5ff; color: #409eff; }}
  .nav-item.active {{ background: #ecf5ff; color: #409eff; }}
  .nav-item.hidden {{ display: none; }}
  .count {{ color: #c0c4cc; font-size: 12px; }}
  /* 方法徽标 */
  .m-badge {{ display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; color: #fff; min-width: 50px; text-align: center; }}
  .m-get {{ background: #67c23a; }}
  .m-post {{ background: #409eff; }}
  .m-put {{ background: #e6a23c; }}
  .m-delete {{ background: #f56c6c; }}
  .m-patch {{ background: #909399; }}
  /* 主内容 */
  .main {{ flex: 1; margin-left: 280px; padding: 24px 32px; max-width: 100%; overflow-x: hidden; }}
  .main-header {{ margin-bottom: 20px; }}
  .main-header h2 {{ font-size: 22px; color: #303133; }}
  .main-header .meta {{ color: #909399; font-size: 13px; margin-top: 4px; }}
  .api-block {{ background: #fff; border: 1px solid #e4e7ed; border-radius: 6px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
  .api-head {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .api-title {{ font-size: 17px; color: #303133; }}
  .api-desc {{ color: #606266; font-size: 13px; margin-bottom: 10px; line-height: 1.6; }}
  .api-url {{ display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #f5f7fa; border-radius: 4px; margin-bottom: 8px; }}
  .url-text {{ font-family: Consolas, Monaco, monospace; font-size: 13px; color: #303133; word-break: break-all; }}
  .api-meta {{ font-size: 12px; color: #909399; margin-bottom: 12px; }}
  .api-meta code {{ background: #f5f7fa; padding: 1px 6px; border-radius: 3px; font-size: 12px; }}
  .section {{ margin-top: 14px; }}
  .section h4 {{ font-size: 14px; color: #303133; margin-bottom: 8px; border-left: 3px solid #409eff; padding-left: 8px; }}
  .ct {{ color: #909399; font-weight: normal; font-size: 12px; }}
  table.tbl {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  table.tbl th, table.tbl td {{ border: 1px solid #ebeef5; padding: 8px 10px; text-align: left; }}
  table.tbl th {{ background: #f5f7fa; color: #606266; font-weight: 500; }}
  table.tbl td code {{ background: #f5f7fa; padding: 1px 6px; border-radius: 3px; font-family: Consolas, Monaco, monospace; }}
  pre.code {{ background: #1e1e1e; color: #d4d4d4; padding: 14px; border-radius: 4px; overflow-x: auto; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.5; }}
  .empty {{ padding: 40px; text-align: center; color: #c0c4cc; }}
  @media (max-width: 768px) {{
    .sidebar {{ position: relative; width: 100%; height: auto; }}
    .main {{ margin-left: 0; }}
  }}
</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>{html.escape(title)}</h1>
      <input class="search-box" id="searchBox" placeholder="搜索接口..." oninput="filterApi()">
    </div>
    <div class="stats">共 {total} 个接口 · 生成于 {gen_time}</div>
    <nav class="nav">
      {sidebar}
    </nav>
  </aside>
  <main class="main">
    <div class="main-header">
      <h2>{html.escape(title)}</h2>
      <div class="meta">由 TestMaster 用例自动生成 · 文档即用例</div>
    </div>
    {no_data}
    {details}
  </main>
</div>
<script>
  // 分组折叠
  function toggleGroup(id) {{
    var el = document.getElementById(id);
    if (el && el.parentElement) el.parentElement.classList.toggle('collapsed');
  }}
  // 选中接口高亮
  function selectApi(id) {{
    document.querySelectorAll('.nav-item').forEach(function(n){{ n.classList.remove('active'); }});
    event.currentTarget.classList.add('active');
    var target = document.getElementById(id);
    if (target) target.scrollIntoView({{behavior:'smooth', block:'start'}});
  }}
  // 搜索过滤
  function filterApi() {{
    var kw = document.getElementById('searchBox').value.trim().toLowerCase();
    document.querySelectorAll('.nav-item').forEach(function(item) {{
      var label = item.textContent.toLowerCase();
      var blockId = item.getAttribute('onclick').match(/'([^']+)'/);
      var blockText = blockId ? (document.getElementById(blockId[1])||{{}}).textContent.toLowerCase() : '';
      var match = !kw || label.indexOf(kw) > -1 || blockText.indexOf(kw) > -1;
      item.classList.toggle('hidden', !match);
    }});
  }}
</script>
</body>
</html>"""
