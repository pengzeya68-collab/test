"""
接口用例路由
- 分页查询、模糊搜索
- 增删改查
- 用例执行历史（查询 auto_test.db）
"""
from fastapi import APIRouter, Depends, Query
from fastapi_backend.core.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import ApiCase, ApiGroup
from fastapi_backend.schemas.cases import (
    ApiCaseCreate,
    ApiCaseUpdate,
    ApiCaseResponse,
    ApiCaseListResponse,
)

router = APIRouter(prefix="/api/v1/cases", tags=["接口用例"])


@router.get("/", response_model=ApiCaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    group_id: int = Query(None, description="按分组筛选"),
    keyword: str = Query(None, description="搜索关键词（名称/URL）"),
    method: str = Query(None, description="按方法筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取接口用例列表，支持分页、搜索、筛选"""

    # 构建查询条件
    query = select(ApiCase)

    if group_id:
        query = query.where(ApiCase.group_id == group_id)

    if keyword:
        query = query.where(
            or_(
                ApiCase.name.contains(keyword),
                ApiCase.url.contains(keyword),
                ApiCase.description.contains(keyword)
            )
        )

    if method:
        query = query.where(ApiCase.method == method)

    # 获取总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # 分页
    query = query.order_by(ApiCase.updated_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    cases = result.scalars().all()

    # 计算总页数
    pages = (total + size - 1) // size if size > 0 else 0

    return {
        "total": total,
        "items": cases,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/all", response_model=list[ApiCaseResponse])
async def get_all_cases(
    group_id: int = Query(None, description="按分组筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取所有用例（用于选择）"""
    query = select(ApiCase).order_by(ApiCase.updated_at.desc())
    if group_id:
        query = query.where(ApiCase.group_id == group_id)
    result = await db.execute(query)
    cases = result.scalars().all()
    return cases


@router.get("/{case_id}", response_model=ApiCaseResponse)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个用例详情"""
    result = await db.execute(select(ApiCase).filter(ApiCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundException("用例不存在")
    return case


@router.post("/", response_model=ApiCaseResponse, status_code=201)
async def create_case(case_in: ApiCaseCreate, db: AsyncSession = Depends(get_db)):
    """创建新用例"""
    case = ApiCase(**case_in.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.put("/{case_id}", response_model=ApiCaseResponse)
async def update_case(
    case_id: int,
    case_in: ApiCaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新用例"""
    result = await db.execute(select(ApiCase).filter(ApiCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundException("用例不存在")

    for field, value in case_in.model_dump(exclude_unset=True).items():
        setattr(case, field, value)

    await db.commit()
    await db.refresh(case)
    return case


@router.delete("/{case_id}")
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """删除用例"""
    result = await db.execute(select(ApiCase).filter(ApiCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundException("用例不存在")

    await db.delete(case)
    await db.commit()
    return {"success": True, "message": "删除成功"}


@router.get("/{case_id}/history")
async def get_case_history(case_id: int):
    """获取用例执行历史（从 auto_test.db 查询）"""
    from fastapi_backend.core.autotest_database import async_session as autotest_session
    from fastapi_backend.models.autotest import AutoTestHistory

    async with autotest_session() as session:
        result = await session.execute(
            select(AutoTestHistory)
            .filter(AutoTestHistory.case_id == case_id)
            .order_by(AutoTestHistory.created_at.desc())
            .limit(20)
        )
        history = result.scalars().all()
        return [
            {
                "id": h.id,
                "case_id": h.case_id,
                "status": h.status,
                "execution_time": h.execution_time,
                "report_url": h.report_url,
                "error_message": h.error_message,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ]
