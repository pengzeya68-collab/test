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
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestCase, AutoTestHistory, AutoTestScenarioStep
from fastapi_backend.schemas.autotest import (
    AutoTestCaseCreate,
    AutoTestCaseUpdate,
)

router = APIRouter(prefix="/api/auto-test/cases", tags=["AutoTest-用例"], dependencies=[Depends(get_current_user)])


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
        "body_type": getattr(case, 'body_type', 'none'),
        "content_type": getattr(case, 'content_type', 'application/json'),
        "payload": case.payload,
        "assert_rules": case.assert_rules,
        "extractors": case.extractors,
        "description": case.description,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }


@router.get("")
async def list_cases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    group_id: Optional[int] = Query(None, description="按分组筛选"),
    keyword: str = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    """获取接口用例列表，支持分页、搜索、筛选"""
    query = select(AutoTestCase)

    if group_id:
        query = query.where(AutoTestCase.group_id == group_id)
    if keyword:
        query = query.where(
            or_(
                AutoTestCase.name.contains(keyword),
                AutoTestCase.url.contains(keyword),
                AutoTestCase.description.contains(keyword),
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
        # 查询每个 case_id 的最新历史记录
        # 先获取所有 case_id 的最大 created_at
        max_time_subq = (
            select(AutoTestHistory.case_id, func.max(AutoTestHistory.created_at).label("max_time"))
            .where(AutoTestHistory.case_id.in_(case_ids))
            .group_by(AutoTestHistory.case_id)
            .subquery()
        )
        latest_history_stmt = select(AutoTestHistory).join(
            max_time_subq,
            (AutoTestHistory.case_id == max_time_subq.c.case_id) &
            (AutoTestHistory.created_at == max_time_subq.c.max_time)
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
    db: AsyncSession = Depends(get_db),
):
    """获取所有用例（用于选择）"""
    query = select(AutoTestCase).order_by(AutoTestCase.updated_at.desc())
    if group_id:
        query = query.where(AutoTestCase.group_id == group_id)
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
            (AutoTestHistory.case_id == max_time_subq.c.case_id) &
            (AutoTestHistory.created_at == max_time_subq.c.max_time)
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
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个用例详情"""
    result = await db.execute(select(AutoTestCase).filter(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    # 查询最近的执行历史
    history_query = select(AutoTestHistory).where(AutoTestHistory.case_id == case.id).order_by(AutoTestHistory.created_at.desc()).limit(1)
    history_result = await db.execute(history_query)
    last_history = history_result.scalar_one_or_none()
    
    case_dict = _case_to_dict(case)
    case_dict["lastRunStatus"] = last_history.status if last_history else None
    
    return case_dict


@router.post("", status_code=201)
async def create_case(case_in: AutoTestCaseCreate, db: AsyncSession = Depends(get_db)):
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
    # extractors 字段已添加到数据库，不再移除
    case = AutoTestCase(**data)
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return _case_to_dict(case)


@router.put("/{case_id}")
async def update_case(
    case_id: int,
    case_in: AutoTestCaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新用例"""
    # URL格式校验
    if case_in.url is not None and case_in.url != "" and not case_in.url.startswith(("/", "http://", "https://")):
        raise HTTPException(status_code=400, detail="URL格式不正确，必须以/或http://或https://开头")
    
    result = await db.execute(select(AutoTestCase).filter(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    update_data = case_in.model_dump(exclude_unset=True, exclude_none=True)
    if "assertions" in update_data:
        update_data["assert_rules"] = update_data.pop("assertions")
    if update_data.get("folder_id") is not None:
        update_data["group_id"] = update_data.pop("folder_id")
    else:
        update_data.pop("folder_id", None)
    if update_data.get("group_id") in ("", None):
        update_data.pop("group_id", None)
    # extractors 字段已添加到数据库，不再移除

    for field, value in update_data.items():
        setattr(case, field, value)

    await db.commit()
    await db.refresh(case)
    return _case_to_dict(case)


@router.delete("/{case_id}")
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """删除用例（自动解除场景步骤引用）"""
    result = await db.execute(select(AutoTestCase).filter(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 删除引用该用例的场景步骤
    steps_result = await db.execute(
        select(AutoTestScenarioStep).where(AutoTestScenarioStep.api_case_id == case_id)
    )
    for step in steps_result.scalars().all():
        await db.delete(step)

    await db.delete(case)
    await db.commit()
    return {"success": True, "message": "删除成功"}
