"""
AutoTest 用例版本管理路由 - 版本快照、回滚、对比

路径前缀: /api/auto-test/cases/{case_id}/versions
对标 Apifox 接口版本管理：
- 保存当前用例为版本快照
- 查看历史版本列表
- 恢复到指定版本
- 删除版本（不可删除当前版本）
- 深度对比两个版本差异
"""

import json
import logging
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestCase, CaseVersion
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    CaseVersionCreate,
    CaseVersionDiffItem,
    CaseVersionDiffResponse,
    CaseVersionResponse,
)

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auto-test/cases", tags=["AutoTest-用例版本管理"])

# 快照中需要保存的用例字段（与 AutoTestCase 业务字段保持一致，不含 id/created_at 等元数据）
SNAPSHOT_FIELDS: Tuple[str, ...] = (
    "name",
    "method",
    "url",
    "headers",
    "params",
    "body_type",
    "content_type",
    "payload",
    "assert_rules",
    "extractors",
    "description",
    "pre_script",
    "post_script",
    "pre_script_language",
    "post_script_language",
    "response_schema",
)


# ========== 辅助函数 ==========


def _build_snapshot(case: AutoTestCase) -> Dict[str, Any]:
    """从用例对象构建完整快照字典"""
    snapshot: Dict[str, Any] = {}
    for field in SNAPSHOT_FIELDS:
        snapshot[field] = getattr(case, field, None)
    return snapshot


def _apply_snapshot_to_case(case: AutoTestCase, snapshot: Dict[str, Any]) -> None:
    """将快照数据写回用例对象（仅业务字段，不覆盖 id/user_id 等元数据）"""
    for field in SNAPSHOT_FIELDS:
        if field in snapshot:
            setattr(case, field, snapshot[field])


async def _get_case_or_404(db: AsyncSession, case_id: int, user_id: int) -> AutoTestCase:
    """获取用例并校验归属，不存在或无权访问返回 404"""
    result = await db.execute(
        select(AutoTestCase).where(AutoTestCase.id == case_id, AutoTestCase.user_id == user_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    return case


async def _get_version_or_404(
    db: AsyncSession, case_id: int, version_id: int
) -> CaseVersion:
    """获取版本并校验 case_id 归属"""
    result = await db.execute(
        select(CaseVersion).where(
            CaseVersion.id == version_id, CaseVersion.case_id == case_id
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return version


async def _generate_auto_version_number(db: AsyncSession, case_id: int) -> str:
    """自动生成下一个版本号 v1/v2/v3..."""
    result = await db.execute(
        select(func.count()).select_from(
            select(CaseVersion).where(CaseVersion.case_id == case_id).subquery()
        )
    )
    count = result.scalar_one()
    return f"v{count + 1}"


async def _set_current_version(
    db: AsyncSession, case_id: int, version_id: int, version_number: str
) -> None:
    """将指定版本设为当前版本：先清除该 case 其他版本的 is_current，再置位目标版本"""
    await db.execute(
        update(CaseVersion)
        .where(CaseVersion.case_id == case_id, CaseVersion.is_current.is_(True))
        .values(is_current=False)
    )
    await db.execute(
        update(CaseVersion)
        .where(CaseVersion.id == version_id)
        .values(is_current=True)
    )
    # 同步冗余字段到用例表，便于列表查询当前版本号
    await db.execute(
        update(AutoTestCase)
        .where(AutoTestCase.id == case_id)
        .values(current_version=version_number)
    )


# ========== 深度 diff 实现 ==========


def _deep_diff(
    old: Any,
    new: Any,
    diffs: List[CaseVersionDiffItem],
    path: str = "",
) -> None:
    """递归对比两个值，差异追加到 diffs 列表。

    - 字典：按键逐一对比，新增键 added，删除键 removed，共有键递归
    - 列表：按下标对比，长度不同部分按 added/removed 处理
    - 标量：值不同则 modified
    """
    # 类型不同直接判定为 modified（除非其中一方为 None 表示缺失，已在调用处处理）
    if isinstance(old, dict) and isinstance(new, dict):
        old_keys = set(old.keys())
        new_keys = set(new.keys())
        # 新增的键
        for key in sorted(new_keys - old_keys):
            child_path = f"{path}.{key}" if path else str(key)
            diffs.append(
                CaseVersionDiffItem(
                    field=child_path,
                    old_value=None,
                    new_value=new[key],
                    change_type="added",
                )
            )
        # 删除的键
        for key in sorted(old_keys - new_keys):
            child_path = f"{path}.{key}" if path else str(key)
            diffs.append(
                CaseVersionDiffItem(
                    field=child_path,
                    old_value=old[key],
                    new_value=None,
                    change_type="removed",
                )
            )
        # 共有键递归
        for key in sorted(old_keys & new_keys):
            child_path = f"{path}.{key}" if path else str(key)
            _deep_diff(old[key], new[key], diffs, child_path)
        return

    if isinstance(old, list) and isinstance(new, list):
        max_len = max(len(old), len(new))
        for idx in range(max_len):
            child_path = f"{path}[{idx}]"
            if idx >= len(old):
                # 新列表更长：新增元素
                diffs.append(
                    CaseVersionDiffItem(
                        field=child_path,
                        old_value=None,
                        new_value=new[idx],
                        change_type="added",
                    )
                )
            elif idx >= len(new):
                # 旧列表更长：删除元素
                diffs.append(
                    CaseVersionDiffItem(
                        field=child_path,
                        old_value=old[idx],
                        new_value=None,
                        change_type="removed",
                    )
                )
            else:
                _deep_diff(old[idx], new[idx], diffs, child_path)
        return

    # 标量或类型不同的根值比较
    if old != new:
        diffs.append(
            CaseVersionDiffItem(
                field=path or "(root)",
                old_value=old,
                new_value=new,
                change_type="modified",
            )
        )


def _version_brief(version: CaseVersion) -> Dict[str, Any]:
    """生成版本摘要信息（不含完整快照，避免响应过大）"""
    return {
        "id": version.id,
        "version_number": version.version_number,
        "version_label": version.version_label,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


# ========== API 端点 ==========


@router.get("/{case_id}/versions")
async def list_case_versions(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用例的所有版本列表（按创建时间倒序，不返回完整 snapshot 减小响应体积）"""
    case = await _get_case_or_404(db, case_id, current_user.id)

    result = await db.execute(
        select(CaseVersion)
        .where(CaseVersion.case_id == case_id)
        .order_by(CaseVersion.created_at.desc(), CaseVersion.id.desc())
    )
    versions = result.scalars().all()

    return {
        "case_id": case_id,
        "current_version": case.current_version,
        "total": len(versions),
        "items": [
            {
                "id": v.id,
                "case_id": v.case_id,
                "version_number": v.version_number,
                "version_label": v.version_label,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "is_current": v.is_current,
            }
            for v in versions
        ],
    }


@router.post("/{case_id}/versions", status_code=201, response_model=CaseVersionResponse)
async def create_case_version(
    case_id: int,
    body: CaseVersionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新版本：将当前用例数据保存为快照。

    - version_number 留空时自动递增生成 v1/v2/v3...
    - 同一 case_id 下版本号唯一，冲突返回 409
    - 首次保存版本自动作为当前版本
    """
    case = await _get_case_or_404(db, case_id, current_user.id)

    version_number = (body.version_number or "").strip()
    if not version_number:
        version_number = await _generate_auto_version_number(db, case_id)

    snapshot_data = _build_snapshot(case)

    version = CaseVersion(
        case_id=case_id,
        version_number=version_number,
        version_label=body.version_label,
        snapshot=json.dumps(snapshot_data, ensure_ascii=False, default=str),
        created_by=current_user.id,
        is_current=False,
    )
    db.add(version)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail=f"版本号 '{version_number}' 已存在，请使用其他版本号"
        )

    # 将新版本设为当前版本（首次保存亦然，符合"最新即当前"语义）
    await _set_current_version(db, case_id, version.id, version_number)
    await db.commit()
    await db.refresh(version)

    _logger.info(
        "用户 %s 为用例 %s 创建版本 %s(%s)",
        current_user.id,
        case_id,
        version.id,
        version_number,
    )
    return CaseVersionResponse(
        id=version.id,
        case_id=version.case_id,
        version_number=version.version_number,
        version_label=version.version_label,
        snapshot=snapshot_data,
        created_by=version.created_by,
        created_at=version.created_at,
        is_current=True,
    )


# 注意：diff 路由必须定义在 /{version_id} 路由之前，
# 否则 FastAPI 会把 "diff" 当作 version_id(int) 解析，返回 422。
@router.get(
    "/{case_id}/versions/diff",
    response_model=CaseVersionDiffResponse,
)
async def diff_case_versions(
    case_id: int,
    v1: int = Query(..., description="旧版本ID"),
    v2: int = Query(..., description="新版本ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """对比两个版本差异：深度对比嵌套对象和数组，返回差异列表。

    v1 为旧版本，v2 为新版本；返回结果中 old_value 取自 v1，new_value 取自 v2。
    """
    await _get_case_or_404(db, case_id, current_user.id)
    if v1 == v2:
        raise HTTPException(status_code=400, detail="不能与同一版本对比")

    version_old = await _get_version_or_404(db, case_id, v1)
    version_new = await _get_version_or_404(db, case_id, v2)

    try:
        old_snapshot = json.loads(version_old.snapshot) if version_old.snapshot else {}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=500, detail="旧版本快照数据损坏")
    try:
        new_snapshot = json.loads(version_new.snapshot) if version_new.snapshot else {}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=500, detail="新版本快照数据损坏")

    diffs: List[CaseVersionDiffItem] = []
    _deep_diff(old_snapshot, new_snapshot, diffs, "")

    return CaseVersionDiffResponse(
        v1=_version_brief(version_old),
        v2=_version_brief(version_new),
        diffs=diffs,
        total_changes=len(diffs),
        is_identical=len(diffs) == 0,
    )


@router.get("/{case_id}/versions/{version_id}", response_model=CaseVersionResponse)
async def get_case_version(
    case_id: int,
    version_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取特定版本详情（包含完整快照数据）"""
    await _get_case_or_404(db, case_id, current_user.id)
    version = await _get_version_or_404(db, case_id, version_id)

    try:
        snapshot_obj = json.loads(version.snapshot) if version.snapshot else None
    except (json.JSONDecodeError, TypeError):
        snapshot_obj = None

    return CaseVersionResponse(
        id=version.id,
        case_id=version.case_id,
        version_number=version.version_number,
        version_label=version.version_label,
        snapshot=snapshot_obj,
        created_by=version.created_by,
        created_at=version.created_at,
        is_current=version.is_current,
    )


@router.put("/{case_id}/versions/{version_id}/restore", response_model=CaseVersionResponse)
async def restore_case_version(
    case_id: int,
    version_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """恢复到指定版本：将快照数据写回用例，并将该版本标记为当前版本。

    注意：恢复不会改变用例的 id/user_id/created_at 等元数据，
    只覆盖业务字段（method/url/headers/payload/assertions 等）。
    """
    case = await _get_case_or_404(db, case_id, current_user.id)
    version = await _get_version_or_404(db, case_id, version_id)

    try:
        snapshot_obj = json.loads(version.snapshot) if version.snapshot else {}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=500, detail="版本快照数据损坏，无法恢复")

    if not snapshot_obj:
        raise HTTPException(status_code=400, detail="版本快照为空，无法恢复")

    # 将快照写回用例
    _apply_snapshot_to_case(case, snapshot_obj)

    # 切换当前版本标记
    await _set_current_version(db, case_id, version.id, version.version_number)
    await db.commit()
    await db.refresh(case)
    await db.refresh(version)

    _logger.info(
        "用户 %s 将用例 %s 恢复到版本 %s(%s)",
        current_user.id,
        case_id,
        version.id,
        version.version_number,
    )
    return CaseVersionResponse(
        id=version.id,
        case_id=version.case_id,
        version_number=version.version_number,
        version_label=version.version_label,
        snapshot=snapshot_obj,
        created_by=version.created_by,
        created_at=version.created_at,
        is_current=True,
    )


@router.delete("/{case_id}/versions/{version_id}", status_code=204)
async def delete_case_version(
    case_id: int,
    version_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除版本。不允许删除当前版本（is_current=True），需先切换到其他版本。

    若删除的是 case 的最后一个版本，则同时清空 AutoTestCase.current_version。
    """
    await _get_case_or_404(db, case_id, current_user.id)
    version = await _get_version_or_404(db, case_id, version_id)

    if version.is_current:
        raise HTTPException(
            status_code=400,
            detail="不能删除当前版本，请先恢复到其他版本再删除",
        )

    await db.delete(version)

    # 检查是否还有剩余版本；若无则清空冗余字段
    remaining_result = await db.execute(
        select(func.count()).select_from(
            select(CaseVersion).where(CaseVersion.case_id == case_id).subquery()
        )
    )
    remaining = remaining_result.scalar_one()
    if remaining == 0:
        await db.execute(
            update(AutoTestCase)
            .where(AutoTestCase.id == case_id)
            .values(current_version=None)
        )

    await db.commit()
    _logger.info("用户 %s 删除用例 %s 的版本 %s", current_user.id, case_id, version_id)
    return None
