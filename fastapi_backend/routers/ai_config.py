from datetime import datetime
from typing import Optional

import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import AIConfig, User
from fastapi_backend.schemas.common import SuccessResponse, MessageResponse

router = APIRouter(prefix="/api/v1/admin/ai-configs", tags=["AI Config"])


def _make_clean_http_client(timeout: int = 60):
    return httpx.AsyncClient(
        timeout=timeout,
        trust_env=False,
    )


class AIConfigCreate(BaseModel):
    name: str = Field(..., max_length=100)
    provider: str = Field(..., pattern=r"^(minimax|openai|ark|custom)$")
    api_key: str
    base_url: Optional[str] = None
    model: str
    max_tokens: int = 2000
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=60, ge=5, le=300)
    group_id: Optional[str] = None


class AIConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    provider: Optional[str] = Field(None, pattern=r"^(minimax|openai|ark|custom)$")
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)
    group_id: Optional[str] = None


class AIConfigOut(BaseModel):
    id: int
    name: str
    provider: str
    api_key_preview: str
    base_url: Optional[str]
    model: str
    is_active: bool
    max_tokens: int
    temperature: float
    timeout_seconds: int
    group_id: Optional[str]
    quota_total: Optional[int]
    quota_used: Optional[int]
    quota_updated_at: Optional[datetime]
    last_test_at: Optional[datetime]
    last_test_result: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def _mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _config_to_out(cfg: AIConfig) -> AIConfigOut:
    return AIConfigOut(
        id=cfg.id,
        name=cfg.name,
        provider=cfg.provider,
        api_key_preview=_mask_api_key(cfg.api_key),
        base_url=cfg.base_url,
        model=cfg.model,
        is_active=cfg.is_active,
        max_tokens=cfg.max_tokens,
        temperature=cfg.temperature,
        timeout_seconds=cfg.timeout_seconds,
        group_id=cfg.group_id,
        quota_total=cfg.quota_total,
        quota_used=cfg.quota_used,
        quota_updated_at=cfg.quota_updated_at,
        last_test_at=cfg.last_test_at,
        last_test_result=cfg.last_test_result,
        created_at=cfg.created_at,
        updated_at=cfg.updated_at,
    )


@router.get("", response_model=SuccessResponse[list[AIConfigOut]])
async def list_ai_configs(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIConfig).order_by(AIConfig.created_at.desc()))
    configs = result.scalars().all()
    items = [_config_to_out(c) for c in configs]
    return SuccessResponse(data=items, message="获取AI配置列表成功")


@router.post("", response_model=SuccessResponse[AIConfigOut], status_code=status.HTTP_201_CREATED)
async def create_ai_config(
    body: AIConfigCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = AIConfig(
        name=body.name,
        provider=body.provider,
        api_key=body.api_key,
        base_url=body.base_url,
        model=body.model,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        timeout_seconds=body.timeout_seconds,
        group_id=body.group_id,
        is_active=False,
    )
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return SuccessResponse(data=_config_to_out(cfg), message="AI配置创建成功")


@router.put("/{config_id}", response_model=SuccessResponse[AIConfigOut])
async def update_ai_config(
    config_id: int,
    body: AIConfigUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = await db.get(AIConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")

    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "api_key" and value is not None:
            setattr(cfg, field, value)
        elif field != "api_key":
            setattr(cfg, field, value)

    await db.commit()
    await db.refresh(cfg)
    return SuccessResponse(data=_config_to_out(cfg), message="AI配置更新成功")


@router.delete("/{config_id}", response_model=SuccessResponse[MessageResponse])
async def delete_ai_config(
    config_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = await db.get(AIConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")

    if cfg.is_active:
        raise HTTPException(status_code=400, detail="无法删除当前激活的配置，请先切换到其他配置")

    await db.delete(cfg)
    await db.commit()
    return SuccessResponse(data=MessageResponse(message="AI配置删除成功"), message="删除成功")


@router.post("/{config_id}/activate", response_model=SuccessResponse[AIConfigOut])
async def activate_ai_config(
    config_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = await db.get(AIConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")

    result = await db.execute(select(AIConfig).where(AIConfig.is_active == True))
    active_configs = result.scalars().all()
    for ac in active_configs:
        ac.is_active = False

    cfg.is_active = True
    await db.commit()
    await db.refresh(cfg)
    return SuccessResponse(data=_config_to_out(cfg), message=f"已激活配置: {cfg.name}")


@router.post("/{config_id}/test", response_model=SuccessResponse[dict])
async def test_ai_config(
    config_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = await db.get(AIConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")

    http_client = _make_clean_http_client(timeout=cfg.timeout_seconds)

    try:
        from openai import AsyncOpenAI

        client_kwargs = {
            "api_key": cfg.api_key,
            "http_client": http_client,
        }
        base_url = cfg.base_url
        if base_url:
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"
            client_kwargs["base_url"] = base_url

        client = AsyncOpenAI(**client_kwargs)

        extra_body = None
        if cfg.provider == "minimax" and cfg.group_id:
            extra_body = {"group_id": cfg.group_id}

        response = await client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": "你是一个AI助手。"},
                {"role": "user", "content": "请回复：连接测试成功"},
            ],
            temperature=0.1,
            max_tokens=50,
            extra_body=extra_body,
        )

        content = response.choices[0].message.content if response.choices else ""
        model_name = response.model if hasattr(response, "model") else cfg.model

        await client.close()

        cfg.last_test_at = datetime.utcnow()
        cfg.last_test_result = "success"
        await db.commit()

        return SuccessResponse(
            data={
                "status": "success",
                "reply": content,
                "model": model_name,
                "provider": cfg.provider,
            },
            message="AI连接测试成功",
        )
    except Exception as e:
        try:
            await http_client.aclose()
        except Exception:
            pass
        cfg.last_test_at = datetime.utcnow()
        cfg.last_test_result = "failed"
        await db.commit()

        return SuccessResponse(
            data={
                "status": "failed",
                "error": str(e),
                "provider": cfg.provider,
            },
            message=f"AI连接测试失败: {str(e)}",
        )


@router.get("/{config_id}/quota", response_model=SuccessResponse[dict])
async def get_ai_quota(
    config_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = await db.get(AIConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="AI配置不存在")

    if cfg.provider == "minimax":
        try:
            base_url = (cfg.base_url or "https://api.minimax.chat/v1").rstrip("/")
            if not base_url.endswith("/v1"):
                base_url += "/v1"

            async with _make_clean_http_client(timeout=30) as client:
                resp = await client.get(
                    f"{base_url}/user/balance",
                    headers={
                        "Authorization": f"Bearer {cfg.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    total = data.get("data", {}).get("total_balance", None)
                    used = data.get("data", {}).get("used_balance", None)

                    cfg.quota_total = total
                    cfg.quota_used = used
                    cfg.quota_updated_at = datetime.utcnow()
                    await db.commit()

                    return SuccessResponse(
                        data={
                            "provider": "minimax",
                            "total_balance": total,
                            "used_balance": used,
                            "raw": data,
                            "updated_at": cfg.quota_updated_at.isoformat() if cfg.quota_updated_at else None,
                        },
                        message="额度查询成功",
                    )
                else:
                    return SuccessResponse(
                        data={
                            "provider": "minimax",
                            "status": "error",
                            "status_code": resp.status_code,
                            "detail": resp.text[:500],
                        },
                        message="额度查询失败",
                    )
        except Exception as e:
            return SuccessResponse(
                data={"provider": "minimax", "status": "error", "error": str(e)},
                message=f"额度查询异常: {str(e)}",
            )
    else:
        return SuccessResponse(
            data={
                "provider": cfg.provider,
                "status": "unsupported",
                "message": f"{cfg.provider} 暂不支持额度查询",
                "quota_total": cfg.quota_total,
                "quota_used": cfg.quota_used,
                "quota_updated_at": cfg.quota_updated_at.isoformat() if cfg.quota_updated_at else None,
            },
            message="该提供商暂不支持额度查询",
        )


@router.get("/active", response_model=SuccessResponse[Optional[AIConfigOut]])
async def get_active_config(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIConfig).where(AIConfig.is_active == True))
    cfg = result.scalar_one_or_none()
    if not cfg:
        return SuccessResponse(data=None, message="当前没有激活的AI配置")
    return SuccessResponse(data=_config_to_out(cfg), message="获取当前激活配置成功")
