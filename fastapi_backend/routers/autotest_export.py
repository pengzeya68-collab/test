"""
AutoTest 导出路由

功能：
- 导出用例为 OpenAPI 3.0 文档
- 导出用例为 Python requests 代码
- 导出用例为 cURL 命令
- cURL 命令导入
- API 文档生成与分享
"""

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup
from fastapi_backend.services.autotest_export_service import (
    export_curl,
    export_openapi,
    export_python_code,
)
from fastapi_backend.services.curl_parser import parse_curl

router = APIRouter(
    prefix="/api/auto-test",
    tags=["导入导出"],
    dependencies=[Depends(get_current_user)],
)


# ========== Pydantic 模型 ==========


class CurlImportRequest(BaseModel):
    curl_string: str


class ExportRequest(BaseModel):
    case_ids: List[int] = []
    group_id: Optional[int] = None
    format: str = "openapi"  # openapi / python / curl


class ShareDocRequest(BaseModel):
    case_ids: List[int] = []
    group_id: Optional[int] = None
    expires_hours: int = 72


# ========== cURL 导入 ==========


@router.post("/import/curl")
async def import_curl(body: CurlImportRequest):
    """解析 cURL 命令，返回用例数据结构"""
    try:
        result = parse_curl(body.curl_string)
        return {"data": result, "message": "cURL 解析成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cURL 解析失败: {str(e)}")


# ========== 导出功能 ==========


async def _get_cases(case_ids: List[int] = None, group_id: int = None) -> List[dict]:
    """获取用例列表"""
    async with AsyncSessionLocal() as db:
        query = select(AutoTestCase)
        if case_ids:
            query = query.where(AutoTestCase.id.in_(case_ids))
        elif group_id is not None:
            query = query.where(AutoTestCase.group_id == group_id)

        result = await db.execute(query)
        cases = result.scalars().all()

        # 批量获取分组名，避免 N+1 查询
        group_ids = list({c.group_id for c in cases if c.group_id is not None})
        group_map = {}
        if group_ids:
            g_result = await db.execute(select(AutoTestGroup).where(AutoTestGroup.id.in_(group_ids)))
            group_map = {g.id: g.name for g in g_result.scalars().all()}

        items = []
        for c in cases:
            items.append({
                "id": c.id,
                "name": c.name,
                "method": c.method,
                "url": c.url,
                "headers": c.headers,
                "params": c.params,
                "body_type": c.body_type,
                "content_type": c.content_type,
                "payload": c.payload,
                "description": c.description,
                "group_name": group_map.get(c.group_id, "default"),
            })

        return items


@router.post("/export")
async def export_cases(body: ExportRequest):
    """导出用例为指定格式"""
    cases = await _get_cases(body.case_ids, body.group_id)
    if not cases:
        raise HTTPException(status_code=400, detail="没有找到要导出的用例")

    if body.format == "openapi":
        doc = export_openapi(cases)
        return JSONResponse(content=doc)
    elif body.format == "python":
        code = export_python_code(cases)
        return JSONResponse(content={"code": code, "language": "python"})
    elif body.format == "curl":
        curls = export_curl(cases)
        return JSONResponse(content={"curls": curls})
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {body.format}")


# ========== API 文档生成 ==========


@router.post("/api-docs/generate")
async def generate_api_doc(body: ExportRequest):
    """从用例生成 OpenAPI 文档"""
    cases = await _get_cases(body.case_ids, body.group_id)
    if not cases:
        raise HTTPException(status_code=400, detail="没有找到用例")

    doc = export_openapi(cases)
    return {"doc": doc, "message": "文档生成成功"}


# ========== 分享链接（内存存储，带自动清理） ==========

_share_tokens: Dict[str, dict] = {}
_MAX_SHARE_TOKENS = 1000


def _cleanup_expired_tokens():
    """清理过期的分享 token，防止内存泄漏"""
    now = datetime.now(timezone.utc)
    expired = [t for t, info in _share_tokens.items() if datetime.fromisoformat(info["expires"]) < now]
    for t in expired:
        del _share_tokens[t]


@router.post("/api-docs/share")
async def create_share_link(body: ShareDocRequest):
    """创建 API 文档分享链接"""
    cases = await _get_cases(body.case_ids, body.group_id)
    if not cases:
        raise HTTPException(status_code=400, detail="没有找到用例")

    # 清理过期 token 并检查上限
    _cleanup_expired_tokens()
    if len(_share_tokens) >= _MAX_SHARE_TOKENS:
        raise HTTPException(status_code=429, detail="分享链接数量已达上限，请稍后再试")

    doc = export_openapi(cases)
    token = secrets.token_urlsafe(16)
    expires = datetime.now(timezone.utc) + timedelta(hours=body.expires_hours)

    _share_tokens[token] = {
        "doc": doc,
        "expires": expires.isoformat(),
        "case_count": len(cases),
    }

    return {
        "token": token,
        "url": f"/api-docs/view/{token}",
        "expires": expires.isoformat(),
        "case_count": len(cases),
    }


@router.get("/api-docs/shared/{token}", dependencies=[])
async def get_shared_doc(token: str):
    """获取分享的 API 文档（无需登录）"""
    info = _share_tokens.get(token)
    if not info:
        raise HTTPException(status_code=404, detail="分享链接不存在或已过期")

    # 检查过期
    expires = datetime.fromisoformat(info["expires"])
    if datetime.now(timezone.utc) > expires:
        del _share_tokens[token]
        raise HTTPException(status_code=410, detail="分享链接已过期")

    return {"doc": info["doc"], "case_count": info["case_count"]}
