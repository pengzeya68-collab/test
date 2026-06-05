"""
AutoTest 统一路由 - 全局变量管理

路径前缀: /api/auto-test/global-variables
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestGlobalVariable
from fastapi_backend.models.models import User
from fastapi_backend.utils.encryption import encrypt, decrypt


class GlobalVariableCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    value: str = Field(...)
    is_encrypted: bool = False
    description: Optional[str] = None


class GlobalVariableUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    value: Optional[str] = None
    is_encrypted: Optional[bool] = None
    description: Optional[str] = None

router = APIRouter(prefix="/api/auto-test/global-variables", tags=["AutoTest-全局变量"])


def _variable_to_dict(variable):
    """将全局变量对象转为字典"""
    # 对加密的变量值进行解密
    value = variable.value
    if variable.is_encrypted:
        try:
            value = decrypt(value)
        except Exception:
            value = "[解密失败]"
    
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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有全局变量"""
    result = await db.execute(
        select(AutoTestGlobalVariable)
        .where(AutoTestGlobalVariable.user_id == current_user.id)
        .order_by(AutoTestGlobalVariable.name)
    )
    variables = result.scalars().all()
    return [_variable_to_dict(v) for v in variables]


@router.get("/{variable_id}")
async def get_global_variable(
    variable_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个全局变量"""
    result = await db.execute(select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.id == variable_id, AutoTestGlobalVariable.user_id == current_user.id))
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")
    return _variable_to_dict(variable)


@router.post("", status_code=201)
async def create_global_variable(
    variable_in: GlobalVariableCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建全局变量"""
    # 检查变量名是否已存在（同一用户下）
    result = await db.execute(
        select(AutoTestGlobalVariable)
        .where(AutoTestGlobalVariable.name == variable_in.name)
        .where(AutoTestGlobalVariable.user_id == current_user.id)
    )
    existing_variable = result.scalar_one_or_none()
    if existing_variable:
        raise HTTPException(status_code=400, detail="变量名已存在")

    data = variable_in.model_dump()
    # 对加密的变量值进行加密
    if data.get("is_encrypted"):
        data["value"] = encrypt(data["value"])

    data["user_id"] = current_user.id
    variable = AutoTestGlobalVariable(**data)
    db.add(variable)
    await db.commit()
    await db.refresh(variable)
    return _variable_to_dict(variable)


@router.put("/{variable_id}")
async def update_global_variable(
    variable_id: int,
    variable_in: GlobalVariableUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新全局变量"""
    result = await db.execute(select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.id == variable_id, AutoTestGlobalVariable.user_id == current_user.id))
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")

    update_data = variable_in.model_dump(exclude_unset=True)

    # 检查变量名是否已被同一用户的其他变量使用
    if "name" in update_data and update_data["name"] != variable.name:
        result = await db.execute(
            select(AutoTestGlobalVariable)
            .where(AutoTestGlobalVariable.name == update_data["name"])
            .where(AutoTestGlobalVariable.user_id == current_user.id)
        )
        existing_variable = result.scalar_one_or_none()
        if existing_variable:
            raise HTTPException(status_code=400, detail="变量名已存在")

    # 对加密的变量值进行加密
    if "is_encrypted" in update_data or "value" in update_data:
        is_encrypted = update_data.get("is_encrypted", variable.is_encrypted)
        if is_encrypted:
            # 只有当 value 被显式提供时才加密，避免对已加密的值重复加密
            if "value" in update_data:
                update_data["value"] = encrypt(update_data["value"])
        else:
            # 如果从加密改为非加密，需要先解密当前值
            if variable.is_encrypted and "value" not in update_data:
                try:
                    update_data["value"] = decrypt(variable.value)
                except Exception:
                    raise HTTPException(status_code=400, detail="变量值解密失败，请手动输入新值")

    for field, value in update_data.items():
        setattr(variable, field, value)

    await db.commit()
    await db.refresh(variable)
    return _variable_to_dict(variable)


@router.delete("/{variable_id}")
async def delete_global_variable(
    variable_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除全局变量"""
    result = await db.execute(select(AutoTestGlobalVariable).filter(AutoTestGlobalVariable.id == variable_id, AutoTestGlobalVariable.user_id == current_user.id))
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")

    await db.delete(variable)
    await db.commit()
    return {"message": "全局变量删除成功"}


@router.post("/batch")
async def batch_create_global_variables(
    variables_in: List[dict],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量创建全局变量"""
    created_variables = []
    for variable_data in variables_in:
        # 检查变量名是否已存在（同一用户下）
        result = await db.execute(
            select(AutoTestGlobalVariable)
            .where(AutoTestGlobalVariable.name == variable_data["name"])
            .where(AutoTestGlobalVariable.user_id == current_user.id)
        )
        existing_variable = result.scalar_one_or_none()
        if not existing_variable:
            # 对加密的变量值进行加密
            if variable_data.get("is_encrypted"):
                variable_data["value"] = encrypt(variable_data["value"])
            variable_data["user_id"] = current_user.id
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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除全局变量"""
    result = await db.execute(
        delete(AutoTestGlobalVariable)
        .where(AutoTestGlobalVariable.id.in_(variable_ids))
        .where(AutoTestGlobalVariable.user_id == current_user.id)
    )
    await db.commit()
    return {"message": f"成功删除 {result.rowcount} 个全局变量"}
