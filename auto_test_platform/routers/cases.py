"""
用例管理路由
提供用例的增删改查、分页、模糊搜索接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from auto_test_platform.database import get_session
from auto_test_platform.models import ApiCase, ApiGroup
from auto_test_platform.schemas import ApiCaseCreate, ApiCaseUpdate, ApiCaseResponse

router = APIRouter(prefix="/cases", tags=["用例管理"])


@router.get("", response_model=List[ApiCaseResponse])
async def get_cases(
    group_id: Optional[int] = Query(None, description="按分组ID筛选"),
    search: Optional[str] = Query(None, description="模糊搜索（名称或URL）"),
    method: Optional[str] = Query(None, description="按请求方法筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: AsyncSession = Depends(get_session)
):
    """
    获取用例列表

    支持:
    - 按分组筛选 (group_id)
    - 模糊搜索名称或URL (search)
    - 按请求方法筛选 (method)
    - 分页 (page, page_size)
    """
    query = select(ApiCase)

    # 应用筛选条件
    if group_id:
        query = query.where(ApiCase.group_id == group_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                ApiCase.name.like(search_pattern),
                ApiCase.url.like(search_pattern)
            )
        )

    if method:
        query = query.where(ApiCase.method == method.upper())

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar()

    # 应用分页
    query = query.order_by(ApiCase.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    cases = result.scalars().all()

    return cases


@router.post("", response_model=ApiCaseResponse)
async def create_case(case: ApiCaseCreate, session: AsyncSession = Depends(get_session)):
    """
    创建新用例

    - name: 用例名称（必填）
    - group_id: 所属分组ID（必填）
    - method: 请求方法（默认 GET）
    - url: 接口地址（必填，支持 {{variable}} 占位符）
    - headers: 请求头（JSON格式，可选）
    - payload: 请求体（JSON格式，可选）
    - assert_rules: 断言规则（JSON格式，可选）
    - description: 用例描述（可选）
    """
    # 验证分组存在
    result = await session.execute(
        select(ApiGroup).where(ApiGroup.id == case.group_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="分组不存在")

    db_case = ApiCase(**case.model_dump())
    session.add(db_case)
    await session.commit()
    await session.refresh(db_case)
    return db_case


@router.get("/{case_id}", response_model=ApiCaseResponse)
async def get_case(case_id: int, session: AsyncSession = Depends(get_session)):
    """
    获取指定用例详情
    """
    result = await session.execute(
        select(ApiCase).where(ApiCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    return case


@router.put("/{case_id}", response_model=ApiCaseResponse)
async def update_case(
    case_id: int,
    case_update: ApiCaseUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    更新用例信息
    """
    result = await session.execute(
        select(ApiCase).where(ApiCase.id == case_id)
    )
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 验证分组存在（如果指定了新的 group_id）
    if case_update.group_id is not None:
        result = await session.execute(
            select(ApiGroup).where(ApiGroup.id == case_update.group_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="分组不存在")

    update_data = case_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        # 跳过 None 值，避免触发数据库 NOT NULL 约束
        if value is None:
            continue
        setattr(db_case, key, value)

    await session.commit()
    await session.refresh(db_case)
    return db_case


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: int, session: AsyncSession = Depends(get_session)):
    """
    删除用例
    """
    result = await session.execute(
        select(ApiCase).where(ApiCase.id == case_id)
    )
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=404, detail="用例不存在")

    await session.delete(db_case)
    await session.commit()
    return None
