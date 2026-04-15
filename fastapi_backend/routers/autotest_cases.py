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
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup, AutoTestHistory
from fastapi_backend.schemas.autotest import (
    AutoTestCaseCreate,
    AutoTestCaseUpdate,
    CaseExecutionResult,
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


@router.get("/")
async def list_cases(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
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

    query = query.order_by(AutoTestCase.updated_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    cases = result.scalars().all()

    # 获取每个用例的最近执行状态
    cases_with_status = []
    for case in cases:
        # 查询最近的执行历史
        history_query = select(AutoTestHistory).where(AutoTestHistory.case_id == case.id).order_by(AutoTestHistory.created_at.desc()).limit(1)
        history_result = await db.execute(history_query)
        last_history = history_result.scalar_one_or_none()
        
        case_dict = _case_to_dict(case)
        case_dict["lastRunStatus"] = last_history.status if last_history else None
        cases_with_status.append(case_dict)

    pages = (total + size - 1) // size if size > 0 else 0

    return {
        "total": total,
        "items": cases_with_status,
        "page": page,
        "size": size,
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
    
    # 获取每个用例的最近执行状态
    cases_with_status = []
    for case in cases:
        # 查询最近的执行历史
        history_query = select(AutoTestHistory).where(AutoTestHistory.case_id == case.id).order_by(AutoTestHistory.created_at.desc()).limit(1)
        history_result = await db.execute(history_query)
        last_history = history_result.scalar_one_or_none()
        
        case_dict = _case_to_dict(case)
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


@router.post("/", status_code=201)
async def create_case(case_in: AutoTestCaseCreate, db: AsyncSession = Depends(get_db)):
    """创建新用例"""
    data = case_in.model_dump()
    if "assertions" in data:
        data["assert_rules"] = data.pop("assertions")
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
    result = await db.execute(select(AutoTestCase).filter(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    update_data = case_in.model_dump(exclude_unset=True)
    if "assertions" in update_data:
        update_data["assert_rules"] = update_data.pop("assertions")
    # extractors 字段已添加到数据库，不再移除

    for field, value in update_data.items():
        setattr(case, field, value)

    await db.commit()
    await db.refresh(case)
    return _case_to_dict(case)


@router.delete("/{case_id}")
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """删除用例"""
    result = await db.execute(select(AutoTestCase).filter(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    await db.delete(case)
    await db.commit()
    return {"success": True, "message": "删除成功"}
