"""
AutoTest API 文档路由 - 在线 API 文档生成与分享

路径前缀: /api/auto-test/api-docs
功能：
- 从用例生成 OpenAPI 3.0 / Markdown / HTML 文档
- 在线预览 HTML 文档
- 生成持久化分享链接（DB 存储，支持过期与浏览统计）
- 公开访问分享的文档（无需登录）

对标 Apifox 自动 API 文档。
"""

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import ApiDocShare, AutoTestCase
from fastapi_backend.models.models import User
from fastapi_backend.services.api_doc_generator import ApiDocGenerator
from fastapi_backend.services.auth_service import AuthService

# 主路由（需登录）
router = APIRouter(prefix="/api/auto-test/api-docs", tags=["AutoTest-API文档"])

# 公开路由（无需登录，用于分享文档访问）
public_router = APIRouter(
    prefix="/api/auto-test/api-docs",
    tags=["AutoTest-API文档分享"],
)

# 声明额外路由供 router_registry 自动发现
EXTRA_ROUTERS = ["public_router"]


# ========== Pydantic 请求模型 ==========


class DocShareRequest(BaseModel):
    """创建文档分享链接请求"""

    case_ids: List[int] = []
    group_id: Optional[int] = None
    expires_hours: int = 72  # 有效期小时数，1-720
    format: str = "html"  # 文档格式: html/markdown/openapi
    title: Optional[str] = None  # 文档标题
    password: Optional[str] = None  # 可选访问密码，设置后访问需提供

    @field_validator("expires_hours")
    @classmethod
    def validate_expires(cls, v):
        if v < 1:
            return 1
        if v > 720:
            return 720
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        v = (v or "html").lower()
        if v not in ("html", "markdown", "openapi"):
            raise ValueError("format 仅支持 html/markdown/openapi")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        # 密码可选；提供时去除首尾空白，空字符串视为未设置
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if len(v) < 4:
            raise ValueError("分享密码至少 4 个字符")
        if len(v) > 128:
            raise ValueError("分享密码过长（最多 128 个字符）")
        return v


# ========== 工具函数 ==========


def _parse_case_ids(raw: Optional[str]) -> Optional[List[int]]:
    """将逗号分隔的 case_ids 字符串解析为整数列表

    例: "1,2,3" -> [1, 2, 3]；空或无效返回 None
    """
    if not raw:
        return None
    ids: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return ids or None


async def _validate_case_ownership(
    db: AsyncSession, user_id: int, case_ids: Optional[List[int]], group_id: Optional[int]
) -> tuple[Optional[List[int]], Optional[int]]:
    """校验用例归属：若指定 case_ids，过滤掉不属于当前用户的ID

    返回 (有效case_ids, group_id)
    """
    if case_ids:
        result = await db.execute(
            select(AutoTestCase.id).where(
                AutoTestCase.id.in_(case_ids), AutoTestCase.user_id == user_id
            )
        )
        valid_ids = [row[0] for row in result.all()]
        if not valid_ids:
            raise HTTPException(status_code=400, detail="没有找到可用的用例（用例不存在或无权限）")
        return valid_ids, None
    return case_ids, group_id


# ========== 文档生成端点（需登录） ==========


@router.get("/openapi")
async def get_openapi_spec(
    case_ids: Optional[str] = Query(None, description="用例ID列表，逗号分隔，如 1,2,3"),
    group_id: Optional[int] = Query(None, description="按分组过滤"),
    title: str = Query("TestMaster API 文档", description="文档标题"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取 OpenAPI 3.0 规范 JSON"""
    ids = _parse_case_ids(case_ids)
    ids, gid = await _validate_case_ownership(db, current_user.id, ids, group_id)
    spec = await ApiDocGenerator.generate_openapi_spec(
        db, case_ids=ids, group_id=gid, user_id=current_user.id, title=title
    )
    return JSONResponse(content=spec)


@router.get("/markdown")
async def get_markdown_doc(
    case_ids: Optional[str] = Query(None, description="用例ID列表，逗号分隔"),
    group_id: Optional[int] = Query(None, description="按分组过滤"),
    title: str = Query("TestMaster API 文档", description="文档标题"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取 Markdown 格式文档"""
    ids = _parse_case_ids(case_ids)
    ids, gid = await _validate_case_ownership(db, current_user.id, ids, group_id)
    md = await ApiDocGenerator.generate_markdown(
        db, case_ids=ids, group_id=gid, user_id=current_user.id, title=title
    )
    return PlainTextResponse(md, media_type="text/markdown; charset=utf-8")


@router.get("/html")
async def get_html_doc(
    case_ids: Optional[str] = Query(None, description="用例ID列表，逗号分隔"),
    group_id: Optional[int] = Query(None, description="按分组过滤"),
    title: str = Query("TestMaster API 文档", description="文档标题"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取独立 HTML 文档（可离线查看）"""
    ids = _parse_case_ids(case_ids)
    ids, gid = await _validate_case_ownership(db, current_user.id, ids, group_id)
    html_doc = await ApiDocGenerator.generate_html(
        db, case_ids=ids, group_id=gid, user_id=current_user.id, title=title
    )
    return HTMLResponse(content=html_doc)


@router.get("/preview")
async def preview_html_doc(
    case_ids: Optional[str] = Query(None, description="用例ID列表，逗号分隔"),
    group_id: Optional[int] = Query(None, description="按分组过滤"),
    title: str = Query("TestMaster API 文档", description="文档标题"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """在线预览 HTML 文档（返回可在浏览器查看的 HTML）"""
    ids = _parse_case_ids(case_ids)
    ids, gid = await _validate_case_ownership(db, current_user.id, ids, group_id)
    html_doc = await ApiDocGenerator.generate_html(
        db, case_ids=ids, group_id=gid, user_id=current_user.id, title=title
    )
    return HTMLResponse(content=html_doc)


# ========== 分享链接端点（需登录） ==========


@router.post("/share")
async def create_share_link(
    body: DocShareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """生成 API 文档分享链接（持久化存储，支持过期与浏览统计）

    返回 url 为前端分享页面路由，可直接在浏览器打开。
    """
    # D7: case_ids 与 group_id 均为空时拒绝分享，避免误分享全部用例
    if not body.case_ids and body.group_id is None:
        raise HTTPException(
            status_code=400,
            detail="必须指定要分享的用例 case_ids 或分组 group_id，不允许分享全部用例",
        )

    ids, gid = await _validate_case_ownership(db, current_user.id, body.case_ids, body.group_id)

    # D7: 归属校验后再次确认仍非空（防止 case_ids 全部越权被过滤后变为空）
    if not ids and gid is None:
        raise HTTPException(
            status_code=400,
            detail="必须指定要分享的用例 case_ids 或分组 group_id，不允许分享全部用例",
        )

    # 校验用例确实存在（避免分享空文档）
    if ids:
        result = await db.execute(
            select(AutoTestCase.id).where(
                AutoTestCase.id.in_(ids), AutoTestCase.user_id == current_user.id
            )
        )
        valid_ids = [row[0] for row in result.all()]
    elif gid is not None:
        result = await db.execute(
            select(AutoTestCase.id).where(
                AutoTestCase.group_id == gid, AutoTestCase.user_id == current_user.id
            )
        )
        valid_ids = [row[0] for row in result.all()]
    else:
        # D7: 不再走"分享全部用例"分支
        valid_ids = []

    if not valid_ids:
        raise HTTPException(status_code=400, detail="没有找到可分享的用例")

    token = secrets.token_urlsafe(16)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=body.expires_hours)
    title = body.title or "TestMaster API 文档"

    # D4: 可选密码保护，bcrypt 哈希后存储
    password_hash = None
    if body.password:
        password_hash = AuthService.hash_password(body.password)

    share = ApiDocShare(
        token=token,
        title=title,
        case_ids=json.dumps(valid_ids),
        group_id=gid,
        fmt=body.format,
        expires_at=expires_at,
        created_by=current_user.id,
        view_count=0,
        password_hash=password_hash,
    )
    db.add(share)
    await db.commit()
    await db.refresh(share)

    return {
        "token": token,
        "url": f"/#/api-docs-shared/{token}",  # 前端分享页面路由（hash 模式）
        "api_url": f"/api/auto-test/api-docs/shared/{token}",  # 后端公开接口
        "expires": expires_at.isoformat(),
        "expires_hours": body.expires_hours,
        "case_count": len(valid_ids),
        "format": body.format,
        "title": title,
        "password_protected": bool(password_hash),
    }


# ========== 公开访问端点（无需登录） ==========


@public_router.get("/shared/{token}")
async def get_shared_doc(
    token: str,
    db: AsyncSession = Depends(get_db),
    x_share_password: Optional[str] = Header(None, alias="X-Share-Password"),
    password: Optional[str] = Query(None, description="访问密码（用于浏览器直接访问 HTML）"),
):
    """访问分享的 API 文档（公开，无需登录）

    根据 token 查找分享记录，校验过期与密码，返回对应格式的文档内容。
    每次访问自增 view_count。
    """
    result = await db.execute(
        select(ApiDocShare).where(ApiDocShare.token == token)
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")

    # 过期校验
    if share.expires_at is not None:
        expires = share.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=410, detail="分享链接已过期")

    # D4: 密码保护校验（若设置了 password_hash 则必须提供正确密码）
    if share.password_hash:
        provided = x_share_password or password
        if not provided:
            raise HTTPException(status_code=401, detail="该分享已设置密码保护，请提供访问密码")
        if not AuthService.verify_password(provided, share.password_hash):
            raise HTTPException(status_code=403, detail="访问密码不正确")

    # 解析 case_ids
    case_ids: Optional[List[int]] = None
    if share.case_ids:
        try:
            case_ids = json.loads(share.case_ids)
        except (json.JSONDecodeError, TypeError):
            case_ids = None

    fmt = share.fmt or "html"
    title = share.title or "TestMaster API 文档"
    # D8: 公开访问时传入 owner_user_id，用于 group_map 归属过滤
    owner_user_id = share.created_by

    # 先保存响应所需的元信息（避免后续 UPDATE 导致 ORM 对象属性失效）
    expires_at_iso = share.expires_at.isoformat() if share.expires_at else None
    created_at_iso = share.created_at.isoformat() if share.created_at else None

    # 先生成文档（公开访问不传 user_id，case_ids 已在分享时校验归属）
    # 若生成失败则不计入浏览次数
    if fmt == "openapi":
        content = await ApiDocGenerator.generate_openapi_spec(
            db,
            case_ids=case_ids,
            group_id=share.group_id,
            user_id=None,
            title=title,
            owner_user_id=owner_user_id,
        )
    elif fmt == "markdown":
        content = await ApiDocGenerator.generate_markdown(
            db,
            case_ids=case_ids,
            group_id=share.group_id,
            user_id=None,
            title=title,
            owner_user_id=owner_user_id,
        )
    else:
        # html：直接返回 HTML 页面（浏览器访问即可查看）
        html_doc = await ApiDocGenerator.generate_html(
            db,
            case_ids=case_ids,
            group_id=share.group_id,
            user_id=None,
            title=title,
            owner_user_id=owner_user_id,
        )

    # 生成成功后，原子自增浏览次数（避免并发竞态）
    result = await db.execute(
        update(ApiDocShare)
        .where(ApiDocShare.token == token)
        .values(view_count=ApiDocShare.view_count + 1)
        .returning(ApiDocShare.view_count)
    )
    current_view_count = result.scalar_one()
    await db.commit()

    if fmt == "openapi":
        # 直接返回 OpenAPI JSON（便于工具导入）
        response_payload = {
            "token": token,
            "title": title,
            "format": fmt,
            "content": content,
            "view_count": current_view_count,
            "expires_at": expires_at_iso,
            "created_at": created_at_iso,
        }
        return JSONResponse(content=response_payload)
    elif fmt == "markdown":
        response_payload = {
            "token": token,
            "title": title,
            "format": fmt,
            "content": content,
            "view_count": current_view_count,
            "expires_at": expires_at_iso,
            "created_at": created_at_iso,
        }
        return JSONResponse(content=response_payload)
    else:
        # D9: 给 HTML 分享文档增加安全响应头，缓解 XSS 与数据外泄风险
        return HTMLResponse(
            content=html_doc,
            headers={
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'unsafe-inline'; "
                    "style-src 'unsafe-inline'"
                ),
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
            },
        )
