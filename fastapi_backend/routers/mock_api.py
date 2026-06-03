"""
API Mock 服务路由（DB 持久化版）

功能：
- Mock 项目 CRUD
- Mock 规则 CRUD（支持条件响应）
- 动态 Mock 端点
- 请求日志查看
- 从 Swagger 导入规则
- 兼容旧版内存 Mock 接口
"""

import random
import string
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import MockProject, MockRule, MockRequestLog
from fastapi_backend.models.models import User
from fastapi_backend.services.mock_service import mock_engine

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
    response_headers: dict = {}
    response_body: Any = None
    delay_ms: int = 0
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
    condition: Optional[dict] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


# ========== Mock 项目 CRUD ==========


@router.post("/projects")
async def create_project(body: MockProjectCreate, current_user: User = Depends(get_current_active_user)):
    """创建 Mock 项目"""
    async with AsyncSessionLocal() as db:
        # 检查 slug 唯一性
        existing = await db.execute(
            select(MockProject).where(MockProject.base_url_slug == body.base_url_slug)
        )
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
async def list_projects(page: int = 1, size: int = 20, current_user: User = Depends(get_current_active_user)):
    """列出 Mock 项目"""
    async with AsyncSessionLocal() as db:
        total_result = await db.execute(select(func.count(MockProject.id)).where(MockProject.user_id == current_user.id))
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
            rule_count_result = await db.execute(
                select(func.count(MockRule.id)).where(MockRule.project_id == p.id)
            )
            log_count_result = await db.execute(
                select(func.count(MockRequestLog.id)).where(MockRequestLog.project_id == p.id)
            )
            items.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "base_url_slug": p.base_url_slug,
                "is_active": p.is_active,
                "rule_count": rule_count_result.scalar() or 0,
                "log_count": log_count_result.scalar() or 0,
                "created_at": str(p.created_at),
            })

        return {"list": items, "total": total, "page": page, "size": size}


@router.get("/projects/{project_id}")
async def get_project(project_id: int, current_user: User = Depends(get_current_active_user)):
    """获取 Mock 项目详情"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id))
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
async def update_project(project_id: int, body: MockProjectUpdate, current_user: User = Depends(get_current_active_user)):
    """更新 Mock 项目"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if body.name is not None:
            project.name = body.name
        if body.description is not None:
            project.description = body.description
        if body.base_url_slug is not None:
            project.base_url_slug = body.base_url_slug
        if body.is_active is not None:
            project.is_active = body.is_active

        await db.commit()
        return {"message": "更新成功"}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, current_user: User = Depends(get_current_active_user)):
    """删除 Mock 项目"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        await db.delete(project)
        await db.commit()
        return {"message": "删除成功"}


# ========== Mock 规则 CRUD ==========


@router.post("/projects/{project_id}/rules")
async def create_rule(project_id: int, body: MockRuleCreate, current_user: User = Depends(get_current_active_user)):
    """创建 Mock 规则"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

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
    current_user: User = Depends(get_current_active_user),
):
    """列出项目的 Mock 规则"""
    async with AsyncSessionLocal() as db:
        # 校验项目归属
        project_result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        total_result = await db.execute(
            select(func.count(MockRule.id)).where(MockRule.project_id == project_id)
        )
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
                "condition": r.condition,
                "priority": r.priority,
                "is_active": r.is_active,
                "created_at": str(r.created_at),
            }
            for r in rules
        ]

        return {"list": items, "total": total, "page": page, "size": size}


@router.put("/projects/{project_id}/rules/{rule_id}")
async def update_rule(
    project_id: int,
    rule_id: int,
    body: MockRuleUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """更新 Mock 规则"""
    async with AsyncSessionLocal() as db:
        # 校验项目归属
        project_result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        result = await db.execute(
            select(MockRule).where(MockRule.id == rule_id, MockRule.project_id == project_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")

        for field, value in body.dict(exclude_unset=True).items():
            if field == "method" and value:
                value = value.upper()
            setattr(rule, field, value)

        await db.commit()
        return {"message": "规则更新成功"}


@router.delete("/projects/{project_id}/rules/{rule_id}")
async def delete_rule(
    project_id: int,
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """删除 Mock 规则"""
    async with AsyncSessionLocal() as db:
        # 校验项目归属
        project_result = await db.execute(
            select(MockProject).where(MockProject.id == project_id, MockProject.user_id == current_user.id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="项目不存在")

        result = await db.execute(
            select(MockRule).where(MockRule.id == rule_id, MockRule.project_id == project_id)
        )
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
    current_user: User = Depends(get_current_active_user),
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
            query.order_by(MockRequestLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
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
    current_user: User = Depends(get_current_active_user),
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
    "/api/{slug}/{rest_of_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def mock_dynamic_endpoint(request: Request, slug: str, rest_of_path: str):
    """
    动态 Mock 端点 - 根据项目 slug 匹配规则并返回。
    URL格式: /mock/api/{project_slug}/{path}
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

    request_headers = dict(request.headers)

    async with AsyncSessionLocal() as db:
        # 匹配规则
        rule = await mock_engine.match_rule(db, slug, method, path, query_params)

        if not rule:
            elapsed = int((time.time() - start_time) * 1000)
            # 记录未匹配的请求
            project_result = await db.execute(
                select(MockProject).where(MockProject.base_url_slug == slug)
            )
            project = project_result.scalar_one_or_none()
            if project:
                await mock_engine.log_request(
                    db, project.id, None, method, path,
                    request_headers, body_text, 404,
                    '{"error": "No mock rule found"}', elapsed,
                )
            return JSONResponse(
                status_code=404,
                content={"error": "No mock rule found", "path": path, "method": method, "slug": slug},
            )

        # 生成响应
        response_info = await mock_engine.generate_response(rule)
        elapsed = int((time.time() - start_time) * 1000)

        # 记录请求日志
        import json as json_lib
        response_body_str = json_lib.dumps(response_info["body"], ensure_ascii=False) if response_info["body"] else ""
        await mock_engine.log_request(
            db, rule.project_id, rule.id, method, path,
            request_headers, body_text,
            response_info["status"], response_body_str, elapsed,
            rule.name,
        )

        return JSONResponse(
            status_code=response_info["status"],
            content=response_info["body"],
            headers=response_info["headers"],
        )


# ========== 兼容旧版内存 Mock 接口 ==========


_mock_rules_legacy: Dict[str, dict] = {}


def _legacy_rule_key(method: str, path: str, user_id: int) -> str:
    """生成带用户隔离的规则 key"""
    return f"{user_id}:{method}:{path}"


def _generate_mock_data(schema: dict) -> Any:
    """根据 schema 生成 Mock 数据（旧版兼容）"""
    stype = schema.get("type", "string")
    if stype == "string":
        return schema.get(
            "value",
            "mock_string_" + "".join(random.choices(string.ascii_lowercase, k=6)),
        )
    elif stype == "number":
        vmin, vmax = schema.get("min", 0), schema.get("max", 100)
        return schema.get("value", random.randint(vmin, vmax))
    elif stype == "boolean":
        return schema.get("value", random.choice([True, False]))
    elif stype == "array":
        count = schema.get("count", 3)
        item_schema = schema.get("items", {"type": "string"})
        return [_generate_mock_data(item_schema) for _ in range(count)]
    elif stype == "object":
        props = schema.get("properties", {})
        return {k: _generate_mock_data(v) for k, v in props.items()}
    elif stype == "uuid":
        import uuid
        return str(uuid.uuid4())
    elif stype == "timestamp":
        return int(datetime.now(timezone.utc).timestamp())
    elif stype == "email":
        return f"user{random.randint(1, 9999)}@test.com"
    elif stype == "phone":
        return f"1{random.randint(30, 99)}{random.randint(10000000, 99999999)}"
    return None


@router.post("/rules", tags=["Mock旧版兼容"])
async def create_mock_rule_legacy(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
):
    """创建 Mock 规则（旧版兼容）"""
    path = body.get("path", "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="path 不能为空")
    method = body.get("method", "GET").upper()
    key = _legacy_rule_key(method, path, current_user.id)
    _mock_rules_legacy[key] = {
        "key": key,
        "path": path,
        "method": method,
        "status_code": body.get("status_code", 200),
        "response_schema": body.get("response_schema", {}),
        "delay_ms": body.get("delay_ms", 0),
        "description": body.get("description", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user.id,
    }
    return {"message": "Mock 规则已创建", "key": key}


@router.get("/rules", tags=["Mock旧版兼容"])
async def list_mock_rules_legacy(current_user: User = Depends(get_current_active_user)):
    """列出当前用户的 Mock 规则（旧版兼容）"""
    user_rules = [v for v in _mock_rules_legacy.values() if v.get("user_id") == current_user.id]
    return {"rules": user_rules}


@router.delete("/rules/{rule_key:path}", tags=["Mock旧版兼容"])
async def delete_mock_rule_legacy(
    rule_key: str,
    current_user: User = Depends(get_current_active_user),
):
    """删除 Mock 规则（旧版兼容）"""
    rule = _mock_rules_legacy.get(rule_key)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    if rule.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="规则不存在")
    del _mock_rules_legacy[rule_key]
    return {"message": "已删除"}
