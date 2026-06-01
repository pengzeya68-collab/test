"""
AutoTest 统一路由 - 全局变量管理

路径前缀: /api/auto-test/global-variables
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestGlobalVariable
from fastapi_backend.schemas.autotest import GlobalVariableCreate, GlobalVariableUpdate
from fastapi_backend.utils.encryption import encrypt, decrypt

router = APIRouter(
    prefix="/api/auto-test/global-variables",
    tags=["AutoTest-全局变量"],
    dependencies=[Depends(get_current_user)],
)


def _variable_to_dict(variable):
    """将全局变量对象转为字典"""
    # 对加密的变量值进行解密
    value = variable.value
    if variable.is_encrypted:
        value = decrypt(value)

    return {
        "id": variable.id,
        "name": variable.name,
        "value": value,
        "description": variable.description,
        "is_encrypted": variable.is_encrypted,
        "created_at": variable.created_at.isoformat() if variable.created_at else None,
        "updated_at": variable.updated_at.isoformat() if variable.updated_at else None,
    }


@router.get("")
async def get_all_global_variables(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取全局变量列表（分页）"""
    query = select(AutoTestGlobalVariable)
    if keyword:
        query = query.where(AutoTestGlobalVariable.name.contains(keyword))
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(AutoTestGlobalVariable.name).offset(offset).limit(size)
    result = await db.execute(query)
    variables = result.scalars().all()
    return {
        "list": [_variable_to_dict(v) for v in variables],
        "total": total or 0,
        "page": page,
        "size": size,
    }


@router.get("/{variable_id}")
async def get_global_variable(variable_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个全局变量"""
    result = await db.execute(select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.id == variable_id))
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")
    return _variable_to_dict(variable)


@router.post("", status_code=201)
async def create_global_variable(
    variable_in: GlobalVariableCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建全局变量"""
    # 检查变量名是否已存在
    result = await db.execute(select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.name == variable_in.name))
    existing_variable = result.scalar_one_or_none()
    if existing_variable:
        raise HTTPException(status_code=400, detail="变量名已存在")

    data = variable_in.model_dump()
    # 对加密的变量值进行加密
    if data.get("is_encrypted"):
        data["value"] = encrypt(data["value"])

    variable = AutoTestGlobalVariable(**data)
    db.add(variable)
    await db.commit()
    await db.refresh(variable)
    return _variable_to_dict(variable)


@router.put("/{variable_id}")
async def update_global_variable(
    variable_id: int,
    variable_in: GlobalVariableUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新全局变量"""
    result = await db.execute(select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.id == variable_id))
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")

    update_data = variable_in.model_dump(exclude_unset=True)

    # 检查变量名是否已被其他变量使用
    if "name" in update_data and update_data["name"] != variable.name:
        result = await db.execute(
            select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.name == update_data["name"])
        )
        existing_variable = result.scalar_one_or_none()
        if existing_variable:
            raise HTTPException(status_code=400, detail="变量名已存在")

    # 对加密的变量值进行加密
    if "is_encrypted" in update_data or "value" in update_data:
        is_encrypted = update_data.get("is_encrypted", variable.is_encrypted)
        if is_encrypted:
            update_data["value"] = encrypt(update_data.get("value", variable.value))
        else:
            # 如果从加密改为非加密，需要先解密当前值
            if variable.is_encrypted and "value" not in update_data:
                update_data["value"] = decrypt(variable.value)

    for field, value in update_data.items():
        setattr(variable, field, value)

    await db.commit()
    await db.refresh(variable)
    return _variable_to_dict(variable)


@router.delete("/{variable_id}")
async def delete_global_variable(variable_id: int, db: AsyncSession = Depends(get_db)):
    """删除全局变量"""
    result = await db.execute(select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.id == variable_id))
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")

    await db.delete(variable)
    await db.commit()
    return {"message": "全局变量删除成功"}


@router.post("/batch")
async def batch_create_global_variables(
    variables_in: List[dict],
    db: AsyncSession = Depends(get_db),
):
    """批量创建全局变量"""
    created_variables = []
    for variable_data in variables_in:
        # 检查变量名是否已存在
        result = await db.execute(
            select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.name == variable_data["name"])
        )
        existing_variable = result.scalar_one_or_none()
        if not existing_variable:
            # 对加密的变量值进行加密
            if variable_data.get("is_encrypted"):
                variable_data["value"] = encrypt(variable_data["value"])
            variable = AutoTestGlobalVariable(**variable_data)
            db.add(variable)
            created_variables.append(variable)

    if created_variables:
        await db.commit()
        for variable in created_variables:
            await db.refresh(variable)

    return [_variable_to_dict(v) for v in created_variables]


@router.delete("/batch")
async def batch_delete_global_variables(
    variable_ids: List[int],
    db: AsyncSession = Depends(get_db),
):
    """批量删除全局变量"""
    await db.execute(delete(AutoTestGlobalVariable).where(AutoTestGlobalVariable.id.in_(variable_ids)))
    await db.commit()
    return {"message": f"成功删除 {len(variable_ids)} 个全局变量"}
