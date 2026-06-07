"""
测试覆盖率计算服务

统计接口覆盖率、执行通过率，生成热力图数据。
数据来源：AutoTestCase（用例）+ AutoTestHistory（执行记录）
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, distinct, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.autotest import AutoTestCase, AutoTestHistory, AutoTestGroup

_logger = logging.getLogger(__name__)


async def get_coverage_summary(db: AsyncSession, user_id: int = None) -> dict:
    """获取覆盖率汇总统计"""
    # 总接口数（用例中不同的 URL 数量）
    q_total_apis = select(func.count(distinct(AutoTestCase.url)))
    q_total_cases = select(func.count(AutoTestCase.id))
    if user_id is not None:
        q_total_apis = q_total_apis.where(AutoTestCase.user_id == user_id)
        q_total_cases = q_total_cases.where(AutoTestCase.user_id == user_id)

    total_apis = await db.scalar(q_total_apis) or 0
    total_cases = await db.scalar(q_total_cases) or 0

    # 最近 30 天的执行记录
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # 被覆盖的接口数：有执行记录的不同 URL 数量（30天内执行过的）
    q_covered = (
        select(func.count(distinct(AutoTestCase.url)))
        .join(AutoTestHistory, AutoTestHistory.case_id == AutoTestCase.id)
        .where(AutoTestHistory.created_at >= thirty_days_ago)
    )
    if user_id is not None:
        q_covered = q_covered.where(AutoTestCase.user_id == user_id)
    covered_apis = await db.scalar(q_covered) or 0

    q_total_exec = select(func.count(AutoTestHistory.id)).where(AutoTestHistory.created_at >= thirty_days_ago)
    q_passed_exec = select(func.count(AutoTestHistory.id)).where(
        and_(
            AutoTestHistory.created_at >= thirty_days_ago,
            AutoTestHistory.status.in_(["success", "passed"]),
        )
    )
    if user_id is not None:
        q_total_exec = q_total_exec.where(AutoTestHistory.user_id == user_id)
        q_passed_exec = q_passed_exec.where(AutoTestHistory.user_id == user_id)

    total_executions = await db.scalar(q_total_exec) or 0
    passed_executions = await db.scalar(q_passed_exec) or 0

    pass_rate = round(passed_executions / total_executions * 100, 1) if total_executions > 0 else 0

    return {
        "total_apis": total_apis,
        "covered_apis": covered_apis,
        "coverage_rate": round(covered_apis / total_apis * 100, 1) if total_apis > 0 else 0,
        "total_cases": total_cases,
        "total_executions_30d": total_executions,
        "passed_executions_30d": passed_executions,
        "pass_rate_30d": pass_rate,
    }


async def get_coverage_heatmap(db: AsyncSession, days: int = 30, user_id: int = None) -> dict:
    """
    获取覆盖率热力图数据

    X 轴: 时间（天）
    Y 轴: 接口（URL）
    值: 通过/失败/未执行
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    start_date_only = start_date.date()

    cases_query = (
        select(
            AutoTestCase.id,
            AutoTestCase.url,
            AutoTestCase.method,
            AutoTestCase.name,
            AutoTestGroup.name.label("group_name"),
        )
        .outerjoin(AutoTestGroup, AutoTestCase.group_id == AutoTestGroup.id)
        .order_by(AutoTestGroup.name, AutoTestCase.url)
    )
    if user_id is not None:
        cases_query = cases_query.where(AutoTestCase.user_id == user_id)

    cases_result = await db.execute(cases_query)
    cases = cases_result.all()

    if not cases:
        return {"apis": [], "dates": [], "matrix": [], "summary": {}}

    # 去重接口列表（同一 URL 多个用例时收集所有 case_id）
    api_list = []
    seen_urls = {}
    for c in cases:
        key = f"{c.method}:{c.url}"
        if key not in seen_urls:
            seen_urls[key] = len(api_list)
            api_list.append(
                {
                    "id": c.id,
                    "case_ids": [c.id],
                    "url": c.url,
                    "method": c.method,
                    "name": c.name,
                    "group": c.group_name or "未分组",
                }
            )
        else:
            api_list[seen_urls[key]]["case_ids"].append(c.id)

    # 获取最近 N 天的执行记录
    history_query = (
        select(
            AutoTestHistory.case_id,
            AutoTestHistory.status,
            AutoTestHistory.created_at,
        )
        .where(cast(AutoTestHistory.created_at, Date) >= start_date_only)
        .order_by(AutoTestHistory.created_at)
    )
    if user_id is not None:
        history_query = history_query.where(AutoTestHistory.user_id == user_id)

    history_result = await db.execute(history_query)
    history = history_result.all()

    # 构建日期列表
    dates = []
    current = start_date.date()
    end = now.date()
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)

    # 构建 case_id -> url 映射
    case_url_map = {}
    for c in cases:
        case_url_map[c.id] = f"{c.method}:{c.url}"

    # 状态优先级：failed > unknown > passed > none
    status_priority = {"failed": 3, "unknown": 2, "success": 1, "passed": 1, "none": 0}

    matrix = [["none" for _ in dates] for _ in api_list]
    api_idx_map = {f"{a['method']}:{a['url']}": i for i, a in enumerate(api_list)}
    date_idx_map = {d: i for i, d in enumerate(dates)}

    for h in history:
        url_key = case_url_map.get(h.case_id)
        if not url_key:
            continue
        api_idx = api_idx_map.get(url_key)
        if api_idx is None:
            continue
        date_str = h.created_at.date().isoformat()
        date_idx = date_idx_map.get(date_str)
        if date_idx is None:
            continue
        new_status = h.status or "unknown"
        old_status = matrix[api_idx][date_idx]
        if status_priority.get(new_status, 0) > status_priority.get(old_status, 0):
            matrix[api_idx][date_idx] = new_status

    api_stats = []
    for i, api in enumerate(api_list):
        row = matrix[i]
        executed = sum(1 for v in row if v != "none")
        passed = sum(1 for v in row if v in ("passed", "success"))
        failed = sum(1 for v in row if v == "failed")
        api_stats.append(
            {
                **api,
                "executed_days": executed,
                "passed_days": passed,
                "failed_days": failed,
                "pass_rate": round(passed / executed * 100, 1) if executed > 0 else 0,
            }
        )

    return {
        "apis": api_stats,
        "dates": dates,
        "matrix": matrix,
        "summary": {
            "total_apis": len(api_list),
            "total_days": len(dates),
            "start_date": dates[0] if dates else None,
            "end_date": dates[-1] if dates else None,
        },
    }


async def get_api_execution_detail(
    db: AsyncSession,
    case_ids: list[int],
    days: int = 30,
    user_id: int = None,
) -> dict:
    """
    获取接口的执行详情（支持同一 URL 对应多个用例）
    """
    if not case_ids:
        return {"case": None, "records": [], "total": 0}

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    case_query = select(AutoTestCase).where(AutoTestCase.id == case_ids[0])
    if user_id is not None:
        case_query = case_query.where(AutoTestCase.user_id == user_id)
    first_result = await db.execute(case_query)
    first_case = first_result.scalar_one_or_none()
    if not first_case:
        return {"case": None, "records": [], "total": 0}

    history_query = (
        select(AutoTestHistory)
        .where(
            and_(
                AutoTestHistory.case_id.in_(case_ids),
                AutoTestHistory.created_at >= start_date,
            )
        )
        .order_by(AutoTestHistory.created_at.desc())
        .limit(200)
    )
    if user_id is not None:
        history_query = history_query.where(AutoTestHistory.user_id == user_id)

    history_result = await db.execute(history_query)
    history = history_result.scalars().all()

    records = []
    for h in history:
        records.append(
            {
                "id": h.id,
                "status": h.status,
                "response_time": h.execution_time,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "error_message": h.error_message,
            }
        )

    return {
        "case": {
            "id": first_case.id,
            "name": first_case.name,
            "method": first_case.method,
            "url": first_case.url,
            "case_count": len(case_ids),
        },
        "records": records,
        "total": len(records),
    }
