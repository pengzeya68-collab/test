"""
测试执行路由
- 执行测试计划
- 保存测试报告
- 返回执行结果
"""
import json
import time
from datetime import datetime
from typing import List
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import (
    TestPlan,
    TestReport,
    TestReportResult,
    Environment,
    ApiCase,
)

router = APIRouter(prefix="/api", tags=["测试执行"])


def replace_variables(text: str, variables: dict) -> str:
    """替换模板变量 {{variable}}，使用正则替换所有匹配的占位符"""
    if not text or not variables:
        return text
    import re
    # 使用正则替换所有 {{变量名}} 格式，变量名可以包含任意字符（除了 }}）
    def replace_match(match):
        var_name = match.group(1).strip()
        return str(variables.get(var_name, match.group(0)))
    return re.sub(r'\{\{(.*?)\}\}', replace_match, text)


@router.post("/plans/{plan_id}/execute")
async def execute_plan(
    plan_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """执行测试计划并保存报告"""

    # 1. 获取计划信息
    result = await db.execute(select(TestPlan).filter(TestPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    # 2. 获取测试环境和变量
    env_variables = {}
    environment = None
    if plan.environment_id:
        result = await db.execute(select(Environment).filter(Environment.id == plan.environment_id))
        environment = result.scalar_one_or_none()

    if not environment:
        # 获取默认环境
        result = await db.execute(select(Environment).filter(Environment.is_default == True))
        environment = result.scalar_one_or_none()

    if environment:
        if environment.variables:
            try:
                env_variables = json.loads(environment.variables)
            except:
                env_variables = {}
        if environment.base_url and 'base_url' not in env_variables:
            env_variables['base_url'] = environment.base_url

    # 3. 获取计划中的用例
    case_ids = json.loads(plan.case_ids) if plan.case_ids else []
    if not case_ids:
        return {
            "report_id": None,
            "plan_id": plan_id,
            "plan_name": plan.name,
            "total": 0,
            "success": 0,
            "failed": 0,
            "totalTime": 0,
            "results": []
        }

    # 批量获取用例详情
    result = await db.execute(select(ApiCase).filter(ApiCase.id.in_(case_ids)))
    cases = result.scalars().all()
    # 保持原有顺序
    case_map = {c.id: c for c in cases}
    ordered_cases = [case_map[cid] for cid in case_ids if cid in case_map]

    # 4. 创建报告
    report = TestReport(
        user_id=user_id,
        plan_id=plan.id,
        plan_name=plan.name,
        status='running',
        total_count=len(ordered_cases),
        success_count=0,
        failed_count=0,
        total_time=0
    )
    db.add(report)
    await db.flush()  # 获取 report.id

    # 5. 逐个执行用例
    success_count = 0
    failed_count = 0
    total_time = 0
    results = []

    for case in ordered_cases:
        start_time = int(time.time() * 1000)
        result_data = {
            "case_id": case.id,
            "case_name": case.name,
            "method": case.method,
            "url": case.url,
            "status_code": None,
            "success": False,
            "time_ms": 0,
            "error": None,
            "request_headers": case.headers,
            "request_body": case.body,
            "response_body": None,
            "response_headers": None
        }

        try:
            # 变量替换
            url = replace_variables(case.url, env_variables)
            headers = {}
            if case.headers:
                try:
                    headers = json.loads(case.headers)
                    for key in headers:
                        headers[key] = replace_variables(headers[key], env_variables)
                except:
                    pass

            body = case.body or ''
            if body:
                body = replace_variables(body, env_variables)

            # URL 合法性强制校验
            if '{{' in url or '}}' in url:
                elapsed = int(time.time() * 1000) - start_time
                result_data['time_ms'] = elapsed
                result_data['success'] = False
                result_data['error'] = f'环境变量替换失败，URL 中仍存在未替换的占位符: {url}'
                failed_count += 1
                total_time += elapsed
                # 保存结果到数据库
                report_result = TestReportResult(
                    report_id=report.id,
                    case_id=case.id,
                    case_name=case.name,
                    method=case.method,
                    url=case.url,
                    status_code=result_data['status_code'],
                    success=result_data['success'],
                    time_ms=result_data['time_ms'],
                    error=result_data['error'],
                    request_headers=result_data['request_headers'],
                    request_body=result_data['request_body'],
                    response_body=result_data['response_body'],
                    response_headers=result_data['response_headers']
                )
                db.add(report_result)
                results.append(result_data)
                continue

            if not (url.startswith('http://') or url.startswith('https://')):
                elapsed = int(time.time() * 1000) - start_time
                result_data['time_ms'] = elapsed
                result_data['success'] = False
                result_data['error'] = f'生成的 URL 不合法，必须以 http:// 或 https:// 开头: {url}'
                failed_count += 1
                total_time += elapsed
                # 保存结果到数据库
                report_result = TestReportResult(
                    report_id=report.id,
                    case_id=case.id,
                    case_name=case.name,
                    method=case.method,
                    url=case.url,
                    status_code=result_data['status_code'],
                    success=result_data['success'],
                    time_ms=result_data['time_ms'],
                    error=result_data['error'],
                    request_headers=result_data['request_headers'],
                    request_body=result_data['request_body'],
                    response_body=result_data['response_body'],
                    response_headers=result_data['response_headers']
                )
                db.add(report_result)
                results.append(result_data)
                continue

            # 构建请求
            req_kwargs = {
                'method': case.method,
                'url': url,
                'timeout': 30
            }

            if headers:
                req_kwargs['headers'] = headers

            if case.method in ['POST', 'PUT', 'PATCH'] and body:
                if case.body_type == 'json':
                    try:
                        req_kwargs['json'] = json.loads(body)
                    except:
                        req_kwargs['data'] = body
                else:
                    req_kwargs['data'] = body

            # 发送请求
            resp = requests.request(**req_kwargs)
            elapsed = int(time.time() * 1000) - start_time

            result_data['status_code'] = resp.status_code
            result_data['success'] = 200 <= resp.status_code < 300
            result_data['time_ms'] = elapsed
            result_data['response_body'] = resp.text[:10000]  # 限制长度
            result_data['response_headers'] = json.dumps(dict(resp.headers))

            if result_data['success']:
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            elapsed = int(time.time() * 1000) - start_time
            result_data['time_ms'] = elapsed
            result_data['success'] = False
            result_data['error'] = str(e)
            failed_count += 1

        total_time += elapsed

        # 保存结果到数据库
        report_result = TestReportResult(
            report_id=report.id,
            case_id=case.id,
            case_name=case.name,
            method=case.method,
            url=case.url,
            status_code=result_data['status_code'],
            success=result_data['success'],
            time_ms=result_data['time_ms'],
            error=result_data['error'],
            request_headers=result_data['request_headers'],
            request_body=result_data['request_body'],
            response_body=result_data['response_body'],
            response_headers=result_data['response_headers']
        )
        db.add(report_result)
        results.append(result_data)

    # 6. 更新报告状态
    report.total_count = len(ordered_cases)
    report.success_count = success_count
    report.failed_count = failed_count
    report.total_time = total_time
    report.status = 'completed'
    report.executed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(report)

    # 7. 返回结果
    formatted_results = []
    for r in results:
        formatted_results.append({
            "id": r.get("case_id"),
            "name": r.get("case_name"),
            "method": r.get("method"),
            "url": r.get("url"),
            "status": r.get("status_code"),
            "success": r.get("success"),
            "time": r.get("time_ms"),
            "error": r.get("error"),
            "requestHeaders": json.loads(r['request_headers']) if r['request_headers'] else {},
            "requestBody": r['request_body'],
            "response": r['response_body'],
            "responseHeaders": json.loads(r['response_headers']) if r['response_headers'] else None
        })

    return {
        "report_id": report.id,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "total": len(ordered_cases),
        "success": success_count,
        "failed": failed_count,
        "totalTime": total_time,
        "results": formatted_results
    }


@router.get("/reports", response_model=list)
async def list_reports(
    page: int = 1,
    size: int = 20,
    user_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """获取报告列表"""
    query = select(TestReport).order_by(TestReport.executed_at.desc())
    if user_id:
        query = query.where(TestReport.user_id == user_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    reports = result.scalars().all()

    return reports


@router.get("/reports/{report_id}")
async def get_report_detail(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取报告详情"""
    result = await db.execute(select(TestReport).filter(TestReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 获取结果
    from sqlalchemy import select
    result_result = await db.execute(select(TestReportResult).filter(TestReportResult.report_id == report_id))
    results = result_result.scalars().all()

    return {
        "id": report.id,
        "plan_id": report.plan_id,
        "plan_name": report.plan_name,
        "total": report.total_count,
        "success": report.success_count,
        "failed": report.failed_count,
        "total_time": report.total_time,
        "status": report.status,
        "executed_at": report.executed_at,
        "results": [
            {
                "id": r.id,
                "case_id": r.case_id,
                "case_name": r.case_name,
                "method": r.method,
                "url": r.url,
                "status": r.status_code,
                "success": r.success,
                "time": r.time_ms,
                "error": r.error,
                "request_headers": json.loads(r.request_headers) if r.request_headers else {},
                "request_body": r.request_body,
                "response": r.response_body,
                "response_headers": json.loads(r.response_headers) if r.response_headers else None,
                "executed_at": r.executed_at
            } for r in results
        ]
    }


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除报告"""
    result = await db.execute(select(TestReport).filter(TestReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    await db.delete(report)
    await db.commit()
    return {"success": True, "message": "删除成功"}
