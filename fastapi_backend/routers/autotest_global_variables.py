"""
AutoTest 统一路由 - 全局变量管理

路径前缀: /api/auto-test/global-variables
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.deps.auth import get_current_active_user, require_admin
from fastapi_backend.models.autotest import AutoTestGlobalVariable
from fastapi_backend.models.models import User
from fastapi_backend.services.audit_service import AuditService
from fastapi_backend.utils.encryption import encrypt, decrypt


def _mask_variable_value(value: object, is_encrypted: bool) -> str:
    """对加密变量的值进行脱敏，避免审计日志泄露敏感信息。"""
    if value is None:
        return None
    text = str(value)
    if is_encrypted:
        return "***" if text else text
    return text


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


def _variable_to_dict(variable, reveal: bool = False):
    """将全局变量对象转为字典

    Args:
        variable: 全局变量对象
        reveal: 是否返回真实值（仅用于 reveal 端点，需调用方已完成权限校验）
    """
    # 加密变量默认返回 "***" 脱敏，避免明文泄露敏感信息
    value = variable.value
    if variable.is_encrypted:
        if reveal:
            try:
                value = decrypt(value)
            except Exception:
                value = "[解密失败]"
        else:
            value = "***"

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
    """获取单个全局变量（加密变量返回 *** 脱敏）"""
    result = await db.execute(
        select(AutoTestGlobalVariable).filter(
            AutoTestGlobalVariable.id == variable_id, AutoTestGlobalVariable.user_id == current_user.id
        )
    )
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")
    return _variable_to_dict(variable)


@router.get("/{variable_id}/reveal")
async def reveal_global_variable(
    variable_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取单个全局变量的真实值（需管理员权限，仅用于敏感变量查看场景）"""
    result = await db.execute(
        select(AutoTestGlobalVariable).filter(
            AutoTestGlobalVariable.id == variable_id, AutoTestGlobalVariable.user_id == current_user.id
        )
    )
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")
    return _variable_to_dict(variable, reveal=True)


@router.post("", status_code=201)
@audit_log(action="create", resource_type="variable")
async def create_global_variable(
    variable_in: GlobalVariableCreate,
    request: Request,
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
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新全局变量"""
    result = await db.execute(
        select(AutoTestGlobalVariable).filter(
            AutoTestGlobalVariable.id == variable_id, AutoTestGlobalVariable.user_id == current_user.id
        )
    )
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")

    update_data = variable_in.model_dump(exclude_unset=True)

    # 🔥 修复：当 value 为 "***"（脱敏占位符）时，视为前端未修改加密变量值，保留原值不更新
    if update_data.get("value") == "***" and variable.is_encrypted:
        update_data.pop("value", None)

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

    # 捕获变更前快照（对加密变量值脱敏）
    before_encrypted = variable.is_encrypted
    before = {
        k: (_mask_variable_value(getattr(variable, k, None), before_encrypted) if k == "value" else getattr(variable, k, None))
        for k in update_data.keys()
    }

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

    # 捕获变更后快照（对加密变量值脱敏）并写入审计日志
    after_encrypted = variable.is_encrypted
    after = {
        k: (_mask_variable_value(getattr(variable, k, None), after_encrypted) if k == "value" else getattr(variable, k, None))
        for k in update_data.keys()
    }
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="update",
        resource_type="variable",
        resource_id=variable_id,
        resource_name=getattr(variable, "name", None),
        detail={"before": before, "after": after},
        request=request,
    )
    return _variable_to_dict(variable)


@router.delete("/{variable_id}")
@audit_log(action="delete", resource_type="variable", resource_id_param="variable_id")
async def delete_global_variable(
    variable_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除全局变量"""
    result = await db.execute(
        select(AutoTestGlobalVariable).filter(
            AutoTestGlobalVariable.id == variable_id, AutoTestGlobalVariable.user_id == current_user.id
        )
    )
    variable = result.scalar_one_or_none()
    if not variable:
        raise HTTPException(status_code=404, detail="全局变量不存在")

    await db.delete(variable)
    await db.commit()
    return {"message": "全局变量删除成功"}


@router.post("/batch")
async def batch_create_global_variables(
    variables_in: List[GlobalVariableCreate],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量创建全局变量"""
    created_variables = []
    for variable_data in variables_in:
        # 检查变量名是否已存在（同一用户下）
        result = await db.execute(
            select(AutoTestGlobalVariable)
            .where(AutoTestGlobalVariable.name == variable_data.name)
            .where(AutoTestGlobalVariable.user_id == current_user.id)
        )
        existing_variable = result.scalar_one_or_none()
        if not existing_variable:
            data = variable_data.model_dump()
            # 对加密的变量值进行加密
            if data.get("is_encrypted"):
                data["value"] = encrypt(data["value"])
            data["user_id"] = current_user.id
            variable = AutoTestGlobalVariable(**data)
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
    if not variable_ids:
        return {"message": "成功删除 0 个全局变量"}
    result = await db.execute(
        delete(AutoTestGlobalVariable)
        .where(AutoTestGlobalVariable.id.in_(variable_ids))
        .where(AutoTestGlobalVariable.user_id == current_user.id)
    )
    await db.commit()
    return {"message": f"成功删除 {result.rowcount} 个全局变量"}
