"""
AutoTest 导出路由

功能：
- 导出用例为 OpenAPI 3.0 文档
- 导出用例为 Python requests 代码
- 导出用例为 cURL 命令
- cURL 命令导入
- API 文档生成与分享
"""

import json
from typing import Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import and_, func, select

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestGroup,
    AutoTestHistory,
    AutoTestScenario,
    AutoTestScenarioStep,
    MockRule,
    MockProject,
    AutoTestGlobalVariable,
    AutoTestPerformanceExecutionRecord,
    AutoTestPerformanceScenarioStep,
)
from fastapi_backend.models.models import User
from fastapi_backend.services.autotest_export_service import (
    export_curl,
    export_openapi,
    export_python_code,
    export_enhanced_api_doc,
)
from fastapi_backend.services.curl_parser import parse_curl

router = APIRouter(
    prefix="/api/auto-test",
    tags=["导入导出"],
)


# ========== Pydantic 模型 ==========


class CurlImportRequest(BaseModel):
    curl_string: str


class ExportRequest(BaseModel):
    case_ids: List[int] = []
    group_id: Optional[int] = None
    format: str = "openapi"  # openapi / python / curl

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        if v not in ("openapi", "python", "curl"):
            raise ValueError(f"不支持的导出格式: {v}，仅支持 openapi/python/curl")
        return v


# ========== cURL 导入 ==========




@router.post("/import/curl")
async def import_curl(
    body: CurlImportRequest,
    current_user: User = Depends(get_current_active_user),
):
    """解析 cURL 命令，返回用例数据结构"""
    try:
        result = parse_curl(body.curl_string)
        return {"data": result, "message": "cURL 解析成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cURL 解析失败: {str(e)}")


# ========== 导出功能 ==========


async def _get_cases(user_id: int, case_ids: List[int] = None, group_id: int = None) -> List[dict]:
    """获取用例列表（仅返回属于当前用户的用例）"""
    async with AsyncSessionLocal() as db:
        query = select(AutoTestCase).where(AutoTestCase.user_id == user_id)
        if case_ids:
            query = query.where(AutoTestCase.id.in_(case_ids))
        if group_id is not None:
            query = query.where(AutoTestCase.group_id == group_id)

        result = await db.execute(query)
        cases = result.scalars().all()

        # 如果指定了 case_ids，检查是否有不可导出的用例
        if case_ids:
            found_ids = {c.id for c in cases}
            missing_ids = set(case_ids) - found_ids
            if missing_ids:
                import logging

                logging.getLogger(__name__).warning(f"用户 {user_id} 导出时跳过无权限或不存在的用例: {missing_ids}")

        # 批量获取分组名，避免 N+1 查询
        group_ids = list({c.group_id for c in cases if c.group_id is not None})
        group_map = {}
        if group_ids:
            g_result = await db.execute(
                select(AutoTestGroup).where(AutoTestGroup.id.in_(group_ids), AutoTestGroup.user_id == user_id)
            )
            group_map = {g.id: g.name for g in g_result.scalars().all()}

        items = []
        for c in cases:
            items.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "method": c.method,
                    "url": c.url,
                    "headers": c.headers,
                    "params": c.params,
                    "body_type": c.body_type,
                    "content_type": c.content_type,
                    "payload": c.payload,
                    "description": c.description,
                    "group_name": group_map.get(c.group_id, "default"),
                }
            )

        return items


@router.post("/export")
async def export_cases(
    body: ExportRequest,
    current_user: User = Depends(get_current_active_user),
):
    """导出用例为指定格式"""
    cases = await _get_cases(current_user.id, body.case_ids, body.group_id)
    if not cases:
        raise HTTPException(status_code=400, detail="没有找到要导出的用例")

    if body.format == "openapi":
        doc = export_openapi(cases)
        return JSONResponse(content=doc)
    elif body.format == "python":
        code = export_python_code(cases)
        return JSONResponse(content={"code": code, "language": "python"})
    elif body.format == "curl":
        curls = export_curl(cases)
        return JSONResponse(content={"curls": curls})
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {body.format}")


# ========== API 文档生成 ==========


@router.post("/api-docs/generate")
async def generate_api_doc(
    body: ExportRequest,
    current_user: User = Depends(get_current_active_user),
):
    """从用例生成 OpenAPI 文档"""
    cases = await _get_cases(current_user.id, body.case_ids, body.group_id)
    if not cases:
        raise HTTPException(status_code=400, detail="没有找到用例")

    doc = export_openapi(cases)
    return {"doc": doc, "message": "文档生成成功"}


# ========== 分享链接 ==========
# 分享功能已迁移至独立路由 fastapi_backend/routers/autotest_api_docs.py
# （持久化 DB 存储，支持过期与浏览统计，替代原内存存储方案）
# 端点：
#   POST /api/auto-test/api-docs/share        生成分享链接
#   GET  /api/auto-test/api-docs/shared/{token}  公开访问分享文档


# ========== 增强版 API 文档生成 ==========


@router.post("/api-docs/enhanced")
async def generate_enhanced_api_doc(
    body: ExportRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    从用例生成增强版 API 文档（文档即用例）

    自动聚合以下数据：
    - 真实执行历史（请求/响应示例）
    - Mock 服务关联
    - 场景业务流程
    - 性能测试指标
    - 全局变量引用
    """
    user_id = current_user.id

    async with AsyncSessionLocal() as db:
        # 1. 获取用例列表（增强版，包含完整信息）
        query = select(AutoTestCase).where(AutoTestCase.user_id == user_id)
        if body.case_ids:
            query = query.where(AutoTestCase.id.in_(body.case_ids))
        elif body.group_id is not None:
            query = query.where(AutoTestCase.group_id == body.group_id)

        # 限制最大返回数量，防止内存暴涨
        query = query.order_by(AutoTestCase.updated_at.desc()).limit(500)
        result = await db.execute(query)
        cases = result.scalars().all()

        if not cases:
            raise HTTPException(status_code=400, detail="没有找到用例")

        # 获取分组名
        group_ids = list({c.group_id for c in cases if c.group_id is not None})
        group_map = {}
        if group_ids:
            g_result = await db.execute(
                select(AutoTestGroup).where(AutoTestGroup.id.in_(group_ids), AutoTestGroup.user_id == user_id)
            )
            group_map = {g.id: g.name for g in g_result.scalars().all()}

        case_ids = [c.id for c in cases]
        cases_data = []
        for c in cases:
            url = c.url or ""
            parsed_url = url
            # 确保 URL 以 http:// 或 https:// 开头（用于 Mock 匹配）
            if url and not url.startswith(("http://", "https://")):
                parsed_url = (
                    "http://example.com" + url if not url.startswith("/") else "http://example.com/" + url.lstrip("/")
                )
            else:
                parsed_url = url

            path = urlparse(parsed_url).path
            if not path:
                path = url if url.startswith("/") else "/" + url

            cases_data.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "method": c.method,
                    "url": c.url,
                    "path": path,
                    "headers": c.headers or {},
                    "params": c.params or {},
                    "body_type": c.body_type or "none",
                    "content_type": c.content_type or "application/json",
                    "payload": c.payload,
                    "description": c.description,
                    "group_name": group_map.get(c.group_id, "default"),
                }
            )

        # 2. 获取执行历史（每个用例最近 3 次）
        execution_history = {}
        if case_ids:
            history_query = (
                select(AutoTestHistory)
                .where(AutoTestHistory.case_id.in_(case_ids))
                .order_by(AutoTestHistory.case_id, AutoTestHistory.created_at.desc())
            )
            history_result = await db.execute(history_query)
            all_histories = history_result.scalars().all()

            for hist in all_histories:
                if hist.case_id not in execution_history:
                    execution_history[hist.case_id] = []
                if len(execution_history[hist.case_id]) < 3:
                    # response_data 可能是 dict、str 或 None，统一处理
                    resp_data = hist.response_data
                    if isinstance(resp_data, str):
                        try:
                            resp_data = json.loads(resp_data)
                        except (json.JSONDecodeError, ValueError):
                            resp_data = {"raw_response": resp_data}

                    status_code = 200
                    if isinstance(resp_data, dict):
                        status_code = resp_data.get("status_code", 200) or 200

                    execution_history[hist.case_id].append(
                        {
                            "status_code": status_code,
                            "response_data": resp_data,
                            "execution_time": hist.execution_time,
                            "status": hist.status,
                        }
                    )

        # 3. 获取 Mock 服务规则
        mock_query = (
            select(MockRule, MockProject)
            .join(MockProject, MockRule.project_id == MockProject.id)
            .where(MockRule.is_active, MockProject.user_id == user_id)
        )
        mock_result = await db.execute(mock_query)
        mock_rules = {}
        for mock_rule, mock_project in mock_result.all():
            key = f"{mock_rule.method.upper()} {mock_rule.path}"
            mock_rules[key] = {
                "project_name": mock_project.name,
                "rule_name": mock_rule.name or "未命名规则",
                "base_url_slug": mock_project.base_url_slug,
            }

        # 4. 获取场景信息
        scenario_query = (
            select(AutoTestScenario, AutoTestScenarioStep)
            .join(AutoTestScenarioStep, AutoTestScenario.id == AutoTestScenarioStep.scenario_id, isouter=True)
            .where(AutoTestScenario.user_id == user_id)
        )
        scenario_result = await db.execute(scenario_query)
        scenarios_map = {}
        for scenario, step in scenario_result.all():
            if scenario.id not in scenarios_map:
                scenarios_map[scenario.id] = {
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "steps": [],
                }
            if step:
                scenarios_map[scenario.id]["steps"].append(
                    {
                        "step_id": step.id,
                        "api_case_id": step.api_case_id,
                        "step_order": step.step_order,
                    }
                )

        scenarios = list(scenarios_map.values())

        # 5. 获取性能指标（取每个用例最近一次性能测试记录）
        # 使用子查询获取每个 scenario 的最新执行记录，避免笛卡尔积
        if case_ids:
            # 子查询：每个 scenario 的最新执行记录 ID
            latest_perf_subq = (
                select(
                    AutoTestPerformanceExecutionRecord.scenario_id,
                    func.max(AutoTestPerformanceExecutionRecord.id).label("max_id"),
                )
                .group_by(AutoTestPerformanceExecutionRecord.scenario_id)
                .subquery()
            )

            perf_query = (
                select(AutoTestPerformanceScenarioStep, AutoTestPerformanceExecutionRecord)
                .join(
                    AutoTestPerformanceExecutionRecord,
                    and_(
                        AutoTestPerformanceScenarioStep.scenario_id == AutoTestPerformanceExecutionRecord.scenario_id,
                        AutoTestPerformanceExecutionRecord.id == latest_perf_subq.c.max_id,
                    ),
                )
                .join(latest_perf_subq, AutoTestPerformanceScenarioStep.scenario_id == latest_perf_subq.c.scenario_id)
                .where(AutoTestPerformanceScenarioStep.api_case_id.in_(case_ids))
            )
            perf_result = await db.execute(perf_query)
            performance_metrics = {}
            for step, record in perf_result.all():
                if step.api_case_id not in performance_metrics:
                    performance_metrics[step.api_case_id] = {
                        "avg_response_time": record.avg_response_time,
                        "p95_response_time": record.p95_response_time,
                        "p99_response_time": record.p99_response_time,
                        "requests_per_second": record.requests_per_second,
                        "error_rate": record.error_rate,
                    }
        else:
            performance_metrics = {}

        # 6. 获取全局变量
        var_query = select(AutoTestGlobalVariable).where(AutoTestGlobalVariable.user_id == user_id)
        var_result = await db.execute(var_query)
        global_variables = [
            {
                "name": v.name,
                "description": v.description,
                "is_encrypted": v.is_encrypted,
            }
            for v in var_result.scalars().all()
        ]

        # 7. 生成增强文档
        doc = export_enhanced_api_doc(
            cases=cases_data,
            execution_history=execution_history,
            mock_rules=mock_rules,
            scenarios=scenarios,
            performance_metrics=performance_metrics,
            global_variables=global_variables,
        )

        return {
            "doc": doc,
            "message": "增强版文档生成成功",
            # D7: 返回当前文档涵盖的用例 ID 列表，供前端分享时显式传参
            "case_ids": case_ids,
            "stats": {
                "total_cases": len(cases_data),
                "cases_with_history": len(execution_history),
                "cases_with_mock": sum(1 for c in cases_data if f"{c['method'].upper()} {c['path']}" in mock_rules),
                "cases_in_scenarios": len(
                    {
                        c["id"]
                        for c in cases_data
                        if any(step["api_case_id"] == c["id"] for s in scenarios for step in s["steps"])
                    }
                ),
                "cases_with_performance": len(performance_metrics),
            },
        }
