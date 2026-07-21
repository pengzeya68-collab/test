"""
API Mock 服务路由（DB 持久化版）

功能：
- Mock 项目 CRUD
- Mock 规则 CRUD（支持条件响应）
- 动态 Mock 端点
- 请求日志查看
- 从 Swagger 导入规则
- 零配置智能 Mock 兜底
"""

import json
import logging
import math
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.database import AsyncSessionLocal as AuthSessionLocal
from fastapi_backend.core.exceptions import AuthorizationException
from fastapi_backend.core.rbac import get_user_permissions, require_permissions
from fastapi_backend.models.autotest import MockProject, MockRule, MockRequestLog
from fastapi_backend.models.models import User
from fastapi_backend.services.mock_service import _safe_custom_headers, mock_engine

_logger = logging.getLogger(__name__)
_FAULT_TYPES = {"status_error", "delay", "timeout_response", "invalid_json", "custom_headers"}


def _validate_fault_type(value: Optional[str]) -> Optional[str]:
    normalized = (value or "").strip().lower()
    if not normalized:
        return None
    if normalized not in _FAULT_TYPES:
        raise HTTPException(status_code=422, detail="不支持的故障类型")
    return normalized


def _validate_fault_config(fault_type: Optional[str], value: Optional[dict]) -> Optional[dict]:
    """Normalize fault settings at write time so invalid rules cannot be saved."""
    if fault_type is None:
        if value not in (None, {}):
            raise HTTPException(status_code=422, detail="故障参数必须与故障类型一起配置")
        return None
    if value is not None and not isinstance(value, dict):
        raise HTTPException(status_code=422, detail="故障参数必须是 JSON 对象")

    config = dict(value or {})
    probability = config.get("trigger_probability", 1)
    if isinstance(probability, bool):
        raise HTTPException(status_code=422, detail="触发概率必须是 0 到 1 之间的数字")
    try:
        probability = float(probability)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="触发概率必须是 0 到 1 之间的数字") from exc
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise HTTPException(status_code=422, detail="触发概率必须是 0 到 1 之间的数字")
    config["trigger_probability"] = probability

    seed = config.get("random_seed")
    if seed is not None:
        seed = str(seed).strip()
        if len(seed) > 200:
            raise HTTPException(status_code=422, detail="随机种子不能超过 200 个字符")
        if seed:
            config["random_seed"] = seed
        else:
            config.pop("random_seed", None)

    if fault_type in {"delay", "timeout_response"} and "delay_ms" in config:
        try:
            delay_ms = int(config["delay_ms"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="故障延迟必须是 0 到 60000 之间的整数") from exc
        if not 0 <= delay_ms <= 60_000:
            raise HTTPException(status_code=422, detail="故障延迟必须是 0 到 60000 之间的整数")
        config["delay_ms"] = delay_ms

    if fault_type in {"status_error", "invalid_json"} and "status_code" in config:
        try:
            status_code = int(config["status_code"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="故障状态码必须是 100 到 599 的整数") from exc
        minimum = 400 if fault_type == "status_error" else 100
        if not minimum <= status_code <= 599:
            raise HTTPException(status_code=422, detail=f"故障状态码必须是 {minimum} 到 599 的整数")
        config["status_code"] = status_code

    if fault_type == "custom_headers":
        headers = config.get("headers", {})
        if not isinstance(headers, dict) or _safe_custom_headers(headers) != {
            str(name).strip(): str(header).strip() for name, header in headers.items()
        }:
            raise HTTPException(status_code=422, detail="自定义响应头包含不安全或无效的名称/值")
        config["headers"] = _safe_custom_headers(headers)
    return config


async def _require_fault_injection_permission(current_user: User) -> None:
    """Keep controlled failure injection separate from ordinary Mock editing."""
    async with AuthSessionLocal() as auth_db:
        permissions = await get_user_permissions(current_user, auth_db)
    if "*" not in permissions and "mock:fault-inject" not in permissions and "mock:*" not in permissions:
        raise AuthorizationException("权限不足。需要 mock:fault-inject 权限才能配置故障注入")


router = APIRouter(
    prefix="/api/mock",
    tags=["Mock服务"],
)

# 动态 Mock 端点需要独立路由，不能继承父级鉴权
mock_public_router = APIRouter(
    prefix="/api/mock",
    tags=["Mock动态端点"],
)

# 声明额外路由供 router_registry 自动发现
EXTRA_ROUTERS = ["mock_public_router"]


# ========== Pydantic 模型 ==========


class MockProjectCreate(BaseModel):
    name: str
    description: str = ""
    base_url_slug: str
    swagger_source_id: Optional[int] = None


class MockProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_url_slug: Optional[str] = None
    is_active: Optional[bool] = None


class MockRuleCreate(BaseModel):
    method: str = "GET"
    path: str
    name: str = ""
    description: str = ""
    response_status: int = 200
    response_headers: dict = Field(default_factory=dict)
    response_body: Any = None
    delay_ms: int = 0
    fault_type: Optional[str] = None
    fault_config: Optional[dict] = None
    condition: Optional[dict] = None
    priority: int = 0
    is_active: bool = True


class MockRuleUpdate(BaseModel):
    method: Optional[str] = None
    path: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    response_status: Optional[int] = None
    response_headers: Optional[dict] = None
    response_body: Any = None
    delay_ms: Optional[int] = None
    fault_type: Optional[str] = None
    fault_config: Optional[dict] = None
    condition: Optional[dict] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


# ========== Mock 项目 CRUD ==========


@router.post("/projects")
async def create_project(body: MockProjectCreate, current_user: User = Depends(require_permissions("mock:create"))):
    """创建 Mock 项目"""
    async with AsyncSessionLocal() as db:
        # 检查 slug 唯一性
        existing = await db.execute(select(MockProject).where(MockProject.base_url_slug == body.base_url_slug))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="URL标识(slug)已存在")

        project = MockProject(
            name=body.name,
            description=body.description,
            base_url_slug=body.base_url_slug,
            swagger_source_id=body.swagger_source_id,
            user_id=current_user.id,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "base_url_slug": project.base_url_slug,
            "created_at": str(project.created_at),
        }


@router.get("/projects")
async def list_projects(page: int = 1, size: int = 20, current_user: User = Depends(require_permissions("mock:read"))):
    """列出 Mock 项目"""
    async with AsyncSessionLocal() as db:
        total_result = await db.execute(
            select(func.count(MockProject.id)).where(MockProject.user_id == current_user.id)
        )
        total = total_result.scalar() or 0

        result = await db.execute(
            select(MockProject)
            .where(MockProject.user_id == current_user.id)
            .order_by(MockProject.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        projects = result.scalars().all()

        items = []
        for p in projects:
            # 统计规则数和日志数
            rule_count_result = await db.execute(select(func.count(MockRule.id)).where(MockRule.project_id == p.id))
            log_count_result = await db.execute(
                select(func.count(MockRequestLog.id)).where(MockRequestLog.project_id == p.id)
            )
            items.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "base_url_slug": p.base_url_slug,
                    "is_active": p.is_active,
                    "rule_count": rule_count_result.scalar() or 0,
                    "log_count": log_count_result.scalar() or 0,
                    "created_at": str(p.created_at),
                }
            )

        return {"list": items, "total": total, "page": page, "size": size}


@router.get("/projects/{project_id}")
async def get_project(project_id: int, current_user: User = Depends(require_permissions("mock:read"))):
    """获取 Mock 项目详情"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "base_url_slug": project.base_url_slug,
            "is_active": project.is_active,
            "swagger_source_id": project.swagger_source_id,
            "created_at": str(project.created_at),
        }


@router.put("/projects/{project_id}")
async def update_project(
    project_id: int, body: MockProjectUpdate, current_user: User = Depends(require_permissions("mock:update"))
):
    """更新 Mock 项目"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if body.name is not None:
            project.name = body.name
        if body.description is not None:
            project.description = body.description
        if body.base_url_slug is not None and body.base_url_slug != project.base_url_slug:
            # 检查 slug 唯一性
            existing = await db.execute(select(MockProject).where(MockProject.base_url_slug == body.base_url_slug))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="URL标识(slug)已存在")
            project.base_url_slug = body.base_url_slug
        if body.is_active is not None:
            project.is_active = body.is_active

        await db.commit()
        return {"message": "更新成功"}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, current_user: User = Depends(require_permissions("mock:delete"))):
    """删除 Mock 项目（级联删除关联的规则和日志）"""
    from sqlalchemy import delete as sa_delete

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 级联删除关联的请求日志
        rule_ids_subq = select(MockRule.id).where(MockRule.project_id == project_id)
        await db.execute(sa_delete(MockRequestLog).where(MockRequestLog.rule_id.in_(rule_ids_subq)))

        # 级联删除关联的规则
        await db.execute(sa_delete(MockRule).where(MockRule.project_id == project_id))

        # 删除项目
        await db.delete(project)
        await db.commit()
        return {"message": "删除成功"}


# ========== Mock 规则 CRUD ==========


@router.post("/projects/{project_id}/rules")
@audit_log("create_rule", "mock_rule", resource_id_param="project_id")
async def create_rule(
    project_id: int, body: MockRuleCreate, current_user: User = Depends(require_permissions("mock:create"))
):
    """创建 Mock 规则"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        fault_type = _validate_fault_type(body.fault_type)
        if fault_type is not None or body.fault_config not in (None, {}):
            await _require_fault_injection_permission(current_user)
        rule = MockRule(
            project_id=project_id,
            method=body.method.upper(),
            path=body.path,
            name=body.name,
            description=body.description,
            response_status=body.response_status,
            response_headers=body.response_headers,
            response_body=body.response_body,
            delay_ms=body.delay_ms,
            fault_type=fault_type,
            fault_config=_validate_fault_config(fault_type, body.fault_config),
            condition=body.condition,
            priority=body.priority,
            is_active=body.is_active,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return {"id": rule.id, "message": "规则创建成功"}


@router.get("/projects/{project_id}/rules")
async def list_rules(
    project_id: int,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(require_permissions("mock:read")),
):
    """列出项目的 Mock 规则"""
    async with AsyncSessionLocal() as db:
        # 校验项目归属
        project_result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        total_result = await db.execute(select(func.count(MockRule.id)).where(MockRule.project_id == project_id))
        total = total_result.scalar() or 0

        result = await db.execute(
            select(MockRule)
            .where(MockRule.project_id == project_id)
            .order_by(MockRule.priority.desc(), MockRule.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rules = result.scalars().all()

        items = [
            {
                "id": r.id,
                "method": r.method,
                "path": r.path,
                "name": r.name,
                "description": r.description,
                "response_status": r.response_status,
                "response_headers": r.response_headers,
                "response_body": r.response_body,
                "delay_ms": r.delay_ms,
                "fault_type": r.fault_type,
                "fault_config": r.fault_config,
                "condition": r.condition,
                "priority": r.priority,
                "is_active": r.is_active,
                "created_at": str(r.created_at),
            }
            for r in rules
        ]

        return {"list": items, "total": total, "page": page, "size": size}


@router.put("/projects/{project_id}/rules/{rule_id}")
@audit_log("update_rule", "mock_rule", resource_id_param="rule_id")
async def update_rule(
    project_id: int,
    rule_id: int,
    body: MockRuleUpdate,
    current_user: User = Depends(require_permissions("mock:update")),
):
    """更新 Mock 规则"""
    async with AsyncSessionLocal() as db:
        # 校验项目归属
        project_result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        result = await db.execute(select(MockRule).where(MockRule.id == rule_id, MockRule.project_id == project_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")

        updates = body.dict(exclude_unset=True)
        if "fault_type" in updates or "fault_config" in updates:
            await _require_fault_injection_permission(current_user)
        if "fault_type" in updates:
            updates["fault_type"] = _validate_fault_type(updates["fault_type"])
        effective_fault_type = updates.get("fault_type", rule.fault_type)
        if "fault_config" in updates:
            updates["fault_config"] = _validate_fault_config(effective_fault_type, updates["fault_config"])
        elif "fault_type" in updates and effective_fault_type is None:
            updates["fault_config"] = None
        elif "fault_type" in updates:
            updates["fault_config"] = _validate_fault_config(effective_fault_type, rule.fault_config)

        for field, value in updates.items():
            if field == "method" and value:
                value = value.upper()
            setattr(rule, field, value)

        await db.commit()
        return {"message": "规则更新成功"}


@router.delete("/projects/{project_id}/rules/{rule_id}")
async def delete_rule(
    project_id: int,
    rule_id: int,
    current_user: User = Depends(require_permissions("mock:delete")),
):
    """删除 Mock 规则"""
    async with AsyncSessionLocal() as db:
        # 校验项目归属
        project_result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        result = await db.execute(select(MockRule).where(MockRule.id == rule_id, MockRule.project_id == project_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        await db.delete(rule)
        await db.commit()
        return {"message": "规则删除成功"}


# ========== Mock 请求日志 ==========


@router.get("/projects/{project_id}/logs")
async def list_logs(
    project_id: int,
    page: int = 1,
    size: int = 50,
    method: Optional[str] = None,
    current_user: User = Depends(require_permissions("mock:read")),
):
    """查看 Mock 请求日志"""
    async with AsyncSessionLocal() as db:
        # 校验项目归属
        project_result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        query = select(MockRequestLog).where(MockRequestLog.project_id == project_id)
        count_query = select(func.count(MockRequestLog.id)).where(MockRequestLog.project_id == project_id)

        if method:
            query = query.where(MockRequestLog.method == method.upper())
            count_query = count_query.where(MockRequestLog.method == method.upper())

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        result = await db.execute(
            query.order_by(MockRequestLog.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        logs = result.scalars().all()

        items = [
            {
                "id": l.id,
                "method": l.method,
                "path": l.path,
                "request_headers": l.request_headers,
                "request_body": l.request_body,
                "response_status": l.response_status,
                "response_body": l.response_body,
                "response_time_ms": l.response_time_ms,
                "matched_rule_name": l.matched_rule_name,
                "fault_triggered": l.fault_triggered,
                "fault_type": l.fault_type,
                "fault_random_value": l.fault_random_value,
                "created_at": str(l.created_at),
            }
            for l in logs
        ]

        return {"list": items, "total": total, "page": page, "size": size}


# ========== Swagger 导入 ==========


@router.post("/projects/{project_id}/import-swagger")
async def import_swagger(
    project_id: int,
    body: dict,
    current_user: User = Depends(require_permissions("mock:create")),
):
    """从 Swagger 文档导入 Mock 规则"""
    swagger_data = body.get("swagger_data", body)
    # 支持 YAML 字符串
    if isinstance(swagger_data, str):
        try:
            import yaml

            swagger_data = yaml.safe_load(swagger_data)
        except Exception:
            raise HTTPException(status_code=400, detail="YAML 解析失败")
    if not swagger_data or not isinstance(swagger_data, dict):
        raise HTTPException(status_code=400, detail="请提供有效的 Swagger/OpenAPI 数据")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        count = await mock_engine.import_from_swagger(db, project_id, swagger_data)
        return {"message": f"成功导入 {count} 条规则", "count": count}


# ========== 动态 Mock 端点 ==========


@mock_public_router.api_route(
    "/{slug}/{rest_of_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    include_in_schema=False,
)
async def mock_dynamic_endpoint(request: Request, slug: str, rest_of_path: str):
    """
    动态 Mock 端点 - 根据项目 slug 匹配规则并返回。
    URL格式: /api/mock/{project_slug}/{path}
    （路由前缀为 /api/mock，此处路径为 /{slug}/{rest_of_path}，避免出现 /api/mock/api/{slug}/{path} 的双重前缀）
    """
    method = request.method
    path = f"/{rest_of_path}"
    start_time = time.time()

    # 获取请求参数
    query_params = dict(request.query_params)
    body_text = ""
    try:
        body_text = (await request.body()).decode("utf-8", errors="replace")
    except Exception:
        pass

    # M6: 统一小写化 header key，便于条件匹配大小写不敏感查找
    request_headers = {str(k).lower(): v for k, v in request.headers.items()}

    async with AsyncSessionLocal() as db:
        # 构建完整的请求参数字典，支持 query/body/header 条件匹配
        _body_dict = {}
        if body_text:
            try:
                _body_dict = json.loads(body_text)
            except (json.JSONDecodeError, ValueError):
                pass
        _full_request_params = {
            "query": query_params,
            "body": _body_dict if isinstance(_body_dict, dict) else {},
            "header": request_headers,
        }
        # 匹配规则
        match_start = time.time()
        rule = await mock_engine.match_rule(db, slug, method, path, _full_request_params)
        match_elapsed = int((time.time() - match_start) * 1000)

        # M10: 零配置智能 Mock 兜底 —— 未命中规则时不再直接 404
        if not rule:
            # 查询项目（即便未命中规则，也需要项目存在）
            project = await mock_engine.get_project_by_slug(db, slug)
            if not project:
                # 项目不存在或不活跃，仍返回 404
                elapsed = int((time.time() - start_time) * 1000)
                return JSONResponse(
                    status_code=404,
                    content={"error": "Mock project not found", "path": path, "method": method, "slug": slug},
                )
            # 生成兜底响应
            fallback_start = time.time()
            response_info = await mock_engine.generate_fallback_response(db, project, method, path)
            delay_elapsed = int((time.time() - fallback_start) * 1000)
            elapsed = int((time.time() - start_time) * 1000)
            # 记录请求日志（失败时不阻塞响应 - M7）
            try:
                import json as json_lib

                response_body_str = (
                    json_lib.dumps(response_info["body"], ensure_ascii=False) if response_info.get("body") else ""
                )
                await mock_engine.log_request(
                    db,
                    project.id,
                    None,
                    method,
                    path,
                    request_headers,
                    body_text,
                    response_info["status"],
                    response_body_str,
                    elapsed,
                    "(zero-config fallback)",
                )
            except Exception as log_exc:
                _logger.warning("Mock fallback log_request failed: %s", log_exc)
            return JSONResponse(
                status_code=response_info["status"],
                content=response_info["body"],
                headers=response_info.get("headers", {}),
            )

        # 生成响应（M9: 单独计算"延迟耗时"，避免 delay_ms 污染整体统计）
        gen_start = time.time()
        response_info = await mock_engine.generate_response(rule)
        delay_elapsed = int((time.time() - gen_start) * 1000)
        elapsed = int((time.time() - start_time) * 1000)
        # 总响应耗时 = 匹配耗时 + 延迟耗时 + 其他（IO/序列化等极小开销）
        # 这里仍以 wall-clock elapsed 作为 response_time_ms 记录，
        # 但保留 match_elapsed 与 delay_elapsed 便于后续日志扩展
        _ = (match_elapsed, delay_elapsed)

        # 记录请求日志（M7: 失败时仅记录日志不抛出，避免阻塞响应）
        try:
            import json as json_lib

            response_body_str = (
                json_lib.dumps(response_info["body"], ensure_ascii=False) if response_info.get("body") else ""
            )
            await mock_engine.log_request(
                db,
                rule.project_id,
                rule.id,
                method,
                path,
                request_headers,
                body_text,
                response_info["status"],
                response_body_str,
                elapsed,
                rule.name,
                response_info.get("fault"),
            )
        except Exception as log_exc:
            _logger.warning("Mock log_request failed: %s", log_exc)

        if response_info.get("raw_body") is not None:
            return PlainTextResponse(
                status_code=response_info["status"],
                content=response_info["raw_body"],
                headers=response_info["headers"],
                media_type=response_info.get("content_type", "application/json"),
            )
        return JSONResponse(
            status_code=response_info["status"],
            content=response_info["body"],
            headers=response_info["headers"],
        )


# ========== 兼容旧版内存 Mock 接口（已废弃） ==========
#
# 说明（M11 / M12）：
#   旧版内存 Mock 接口与新版 DB 持久化接口互不相通，且删除接口使用复合 key
#   （f"{user_id}:{method}:{path}"）存在越权风险（路径中含 ':' 时 key 解析歧义，
#   亦无法在多用户场景下安全隔离）。统一改为新版基于 DB 的 MockProject/MockRule
#   CRUD 接口。如需"内存级"零配置 Mock，请使用项目级 swagger_source + 零配置
#   智能兜底（M10）。
#
# 已删除的接口：
#   POST   /api/mock/rules                     -> 改用 POST /api/mock/projects/{project_id}/rules
#   GET    /api/mock/rules                     -> 改用 GET  /api/mock/projects/{project_id}/rules
#   DELETE /api/mock/rules/{rule_key:path}     -> 改用 DELETE /api/mock/projects/{project_id}/rules/{rule_id}
