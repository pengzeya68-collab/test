"""
AutoTest 统一路由 - 用例管理

路径前缀: /api/auto-test/cases
映射原 auto_test_platform 的 /api/cases
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestCase, AutoTestHistory, AutoTestScenario, AutoTestScenarioStep
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    AutoTestCaseCreate,
    AutoTestCaseUpdate,
)

router = APIRouter(prefix="/api/auto-test/cases", tags=["AutoTest-用例"])


def _case_to_dict(case):
    """将 case 对象转为字典，兼容数据库中可能存在的非标准字段类型"""
    return {
        "id": case.id,
        "group_id": case.group_id,
        "name": case.name,
        "method": case.method,
        "url": case.url,
        "headers": case.headers,
        "params": case.params,
        "body_type": getattr(case, "body_type", "none"),
        "content_type": getattr(case, "content_type", "application/json"),
        "payload": case.payload,
        "assert_rules": case.assert_rules,
        "extractors": case.extractors,
        "description": case.description,
        # 🔥 修复：必须返回脚本相关字段，否则前端重新加载时 pre_script/post_script 丢失，
        # 版本恢复后再次拉取用例也无法看到恢复的脚本内容
        "pre_script": getattr(case, "pre_script", None),
        "post_script": getattr(case, "post_script", None),
        "pre_script_language": getattr(case, "pre_script_language", "javascript"),
        "post_script_language": getattr(case, "post_script_language", "javascript"),
        "response_schema": getattr(case, "response_schema", None),
        "current_version": getattr(case, "current_version", None),
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }


@router.get("")
async def list_cases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    group_id: Optional[int] = Query(None, description="按分组筛选"),
    keyword: str = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取接口用例列表，支持分页、搜索、筛选"""
    query = select(AutoTestCase).where(AutoTestCase.user_id == current_user.id)

    if group_id is not None:
        query = query.where(AutoTestCase.group_id == group_id)
    if keyword:
        keyword_escaped = keyword.replace("%", "\\%").replace("_", "\\_")
        query = query.where(
            or_(
                AutoTestCase.name.like(f"%{keyword_escaped}%", escape="\\"),
                AutoTestCase.url.like(f"%{keyword_escaped}%", escape="\\"),
                AutoTestCase.description.like(f"%{keyword_escaped}%", escape="\\"),
            )
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(AutoTestCase.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    cases = result.scalars().all()

    # 批量查询每个用例的最近执行状态（避免 N+1 查询）
    case_ids = [case.id for case in cases]
    if case_ids:
        max_time_subq = (
            select(AutoTestHistory.case_id, func.max(AutoTestHistory.created_at).label("max_time"))
            .where(AutoTestHistory.case_id.in_(case_ids))
            .group_by(AutoTestHistory.case_id)
            .subquery()
        )
        latest_history_stmt = select(AutoTestHistory).join(
            max_time_subq,
            (AutoTestHistory.case_id == max_time_subq.c.case_id)
            & (AutoTestHistory.created_at == max_time_subq.c.max_time),
        )
        latest_history_result = await db.execute(latest_history_stmt)
        history_map = {h.case_id: h for h in latest_history_result.scalars().all()}
    else:
        history_map = {}

    cases_with_status = []
    for case in cases:
        case_dict = _case_to_dict(case)
        last_history = history_map.get(case.id)
        case_dict["lastRunStatus"] = last_history.status if last_history else None
        cases_with_status.append(case_dict)

    pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return {
        "total": total,
        "items": cases_with_status,
        "page": page,
        "size": page_size,
        "pages": pages,
    }


@router.get("/all")
async def get_all_cases(
    group_id: int = Query(None, description="按分组筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有用例（用于选择）"""
    query = select(AutoTestCase).where(AutoTestCase.user_id == current_user.id).order_by(AutoTestCase.updated_at.desc())
    if group_id is not None:
        query = query.where(AutoTestCase.group_id == group_id)
    result = await db.execute(query)
    cases = result.scalars().all()

    # 批量查询每个用例的最近执行状态
    case_ids = [case.id for case in cases]
    if case_ids:
        max_time_subq = (
            select(AutoTestHistory.case_id, func.max(AutoTestHistory.created_at).label("max_time"))
            .where(AutoTestHistory.case_id.in_(case_ids))
            .group_by(AutoTestHistory.case_id)
            .subquery()
        )
        latest_history_stmt = select(AutoTestHistory).join(
            max_time_subq,
            (AutoTestHistory.case_id == max_time_subq.c.case_id)
            & (AutoTestHistory.created_at == max_time_subq.c.max_time),
        )
        latest_history_result = await db.execute(latest_history_stmt)
        history_map = {h.case_id: h for h in latest_history_result.scalars().all()}
    else:
        history_map = {}

    cases_with_status = []
    for case in cases:
        case_dict = _case_to_dict(case)
        last_history = history_map.get(case.id)
        case_dict["lastRunStatus"] = last_history.status if last_history else None
        cases_with_status.append(case_dict)

    return cases_with_status


@router.get("/{case_id}")
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个用例详情"""
    result = await db.execute(
        select(AutoTestCase).filter(AutoTestCase.id == case_id, AutoTestCase.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 查询最近的执行历史
    history_query = (
        select(AutoTestHistory)
        .where(AutoTestHistory.case_id == case.id)
        .order_by(AutoTestHistory.created_at.desc())
        .limit(1)
    )
    history_result = await db.execute(history_query)
    last_history = history_result.scalar_one_or_none()

    case_dict = _case_to_dict(case)
    case_dict["lastRunStatus"] = last_history.status if last_history else None

    return case_dict


@router.post("", status_code=201)
async def create_case(
    case_in: AutoTestCaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新用例"""
    # URL格式校验
    if case_in.url and not case_in.url.startswith(("/", "http://", "https://")):
        raise HTTPException(status_code=400, detail="URL格式不正确，必须以/或http://或https://开头")

    data = case_in.model_dump(exclude_none=True)
    if "assertions" in data:
        data["assert_rules"] = data.pop("assertions")
    if data.get("folder_id") is not None:
        data["group_id"] = data.pop("folder_id")
    else:
        data.pop("folder_id", None)
    if data.get("group_id") in ("", None):
        data.pop("group_id", None)
    # 设置用户归属
    data["user_id"] = current_user.id
    case = AutoTestCase(**data)
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return _case_to_dict(case)


@router.put("/{case_id}")
async def update_case(
    case_id: int,
    case_in: AutoTestCaseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用例"""
    # URL格式校验
    if case_in.url is not None and case_in.url != "" and not case_in.url.startswith(("/", "http://", "https://")):
        raise HTTPException(status_code=400, detail="URL格式不正确，必须以/或http://或https://开头")

    result = await db.execute(
        select(AutoTestCase).filter(AutoTestCase.id == case_id, AutoTestCase.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    update_data = case_in.model_dump(exclude_unset=True)
    if "assertions" in update_data:
        update_data["assert_rules"] = update_data.pop("assertions")
    if "folder_id" in update_data:
        folder_val = update_data.pop("folder_id")
        # 仅当 group_id 未被显式设置时，才从 folder_id 派生
        if "group_id" not in update_data:
            update_data["group_id"] = folder_val if folder_val not in ("", None) else None
    # 空字符串视为取消分组，保留 None（显式取消分组）
    if update_data.get("group_id") == "":
        update_data["group_id"] = None

    for field, value in update_data.items():
        if field in ("id", "user_id", "created_at"):
            continue
        setattr(case, field, value)

    await db.commit()
    await db.refresh(case)
    return _case_to_dict(case)


@router.delete("/{case_id}")
async def delete_case(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除用例（自动解除场景步骤引用）"""
    result = await db.execute(
        select(AutoTestCase).filter(AutoTestCase.id == case_id, AutoTestCase.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 先把所有引用该 case 的场景步骤的 api_case_id 置空（不限 user_id），避免跨用户步骤 api_case_id 悬空
    steps_result = await db.execute(
        select(AutoTestScenarioStep).where(AutoTestScenarioStep.api_case_id == case_id)
    )
    for step in steps_result.scalars().all():
        step.api_case_id = None

    await db.delete(case)
    await db.commit()
    return {"success": True, "message": "删除成功"}
