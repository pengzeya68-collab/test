from datetime import datetime, timezone
from typing import Optional

import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
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


# 支持的AI提供商ID列表
SUPPORTED_PROVIDERS = [
    "deepseek", "openai", "minimax", "ark",
    "anthropic", "google", "qwen", "glm",
    "moonshot", "baidu", "hunyuan", "spark",
    "groq", "custom",
]
PROVIDER_PATTERN = r"^(" + "|".join(SUPPORTED_PROVIDERS) + r")$"

class AIConfigCreate(BaseModel):
    name: str = Field(..., max_length=100)
    provider: str = Field(..., pattern=PROVIDER_PATTERN)
    api_key: str
    base_url: Optional[str] = None
    model: str
    max_tokens: int = 2000
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=60, ge=5, le=300)
    group_id: Optional[str] = None


class AIConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    provider: Optional[str] = Field(None, pattern=PROVIDER_PATTERN)
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)
    group_id: Optional[str] = None


PROVIDER_MODEL_SUGGESTIONS = {
    "deepseek": [
        {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash (最新, 快速)", "description": "最新一代模型，快速响应"},
        {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro (高性能)", "description": "高性能版本，适合复杂任务"},
        {"id": "deepseek-chat", "name": "DeepSeek Chat (V3)", "description": "经典DeepSeek V3模型"},
        {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (R1)", "description": "推理专用模型R1"},
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o", "description": "OpenAI最新多模态旗舰"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "轻量快速，性价比高"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "高性能GPT-4"},
        {"id": "o1", "name": "o1 (推理)", "description": "深度推理模型"},
        {"id": "o3-mini", "name": "o3 Mini", "description": "轻量推理模型"},
    ],
    "minimax": [
        {"id": "MiniMax-M2.7", "name": "MiniMax M2.7", "description": "海螺AI最新旗舰模型"},
        {"id": "abab6.5s-chat", "name": "ABAB 6.5S Chat", "description": "MiniMax快速模型"},
        {"id": "MiniMax-T2", "name": "MiniMax T2 (思考)", "description": "支持深度思考模式"},
    ],
    "ark": [
        {"id": "doubao-pro-32k", "name": "豆包 Pro 32K", "description": "字节跳动高性能模型"},
        {"id": "doubao-lite-32k", "name": "豆包 Lite 32K", "description": "字节跳动轻量模型"},
        {"id": "doubao-1.5-pro-256k", "name": "豆包 1.5 Pro 256K", "description": "超长上下文"},
    ],
    "anthropic": [
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Anthropic旗舰，编程/写作顶级"},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "description": "快速轻量版"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "最强推理能力"},
    ],
    "google": [
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "description": "Google最新快速模型"},
        {"id": "gemini-2.0-pro-exp-02-05", "name": "Gemini 2.0 Pro", "description": "Google最强旗舰"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "description": "稳定版旗舰"},
    ],
    "qwen": [
        {"id": "qwen-max", "name": "通义千问 Max", "description": "阿里云最强旗舰"},
        {"id": "qwen-plus", "name": "通义千问 Plus", "description": "性能与速度均衡"},
        {"id": "qwen-turbo", "name": "通义千问 Turbo", "description": "极速响应"},
        {"id": "qwen2.5-72b-instruct", "name": "Qwen2.5 72B", "description": "开源旗舰72B"},
    ],
    "glm": [
        {"id": "glm-4-plus", "name": "GLM-4 Plus", "description": "智谱AI旗舰模型"},
        {"id": "glm-4-flash", "name": "GLM-4 Flash", "description": "快速免费版"},
        {"id": "glm-4-air", "name": "GLM-4 Air", "description": "轻量高性能"},
    ],
    "moonshot": [
        {"id": "moonshot-v1-8k", "name": "Kimi Moonshot v1 8K", "description": "月之暗面标准版"},
        {"id": "moonshot-v1-32k", "name": "Kimi Moonshot v1 32K", "description": "长上下文32K"},
        {"id": "moonshot-v1-128k", "name": "Kimi Moonshot v1 128K", "description": "超长上下文128K"},
    ],
    "baidu": [
        {"id": "ernie-4.0-turbo-8k", "name": "文心一言 4.0 Turbo", "description": "百度最强旗舰"},
        {"id": "ernie-3.5-8k", "name": "文心一言 3.5", "description": "高性能标准版"},
        {"id": "ernie-speed-8k", "name": "文心一言 Speed", "description": "极速响应版"},
    ],
    "hunyuan": [
        {"id": "hunyuan-turbo", "name": "混元 Turbo", "description": "腾讯混元旗舰"},
        {"id": "hunyuan-pro", "name": "混元 Pro", "description": "专业高性能"},
        {"id": "hunyuan-lite", "name": "混元 Lite", "description": "轻量免费版"},
    ],
    "spark": [
        {"id": "generalv3.5", "name": "星火 3.5", "description": "讯飞星火最新版"},
        {"id": "generalv3", "name": "星火 3.0", "description": "讯飞星火稳定版"},
        {"id": "pro-128k", "name": "星火 Pro 128K", "description": "超长上下文版"},
    ],
    "groq": [
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "description": "Meta最新开源旗舰"},
        {"id": "deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill 70B", "description": "DeepSeek R1蒸馏版"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "description": "Mistral混合专家模型"},
    ],
    "custom": [
        {"id": "custom", "name": "自定义模型", "description": "使用自定义API端点"},
    ],
}


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

    model_config = ConfigDict(from_attributes=True)


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
    client = None
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

        cfg.last_test_at = datetime.now(timezone.utc)
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
        cfg.last_test_at = datetime.now(timezone.utc)
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
    finally:
        if client:
            try:
                await client.close()
            except Exception:
                pass
        try:
            await http_client.aclose()
        except Exception:
            pass


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
                    cfg.quota_updated_at = datetime.now(timezone.utc)
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
    elif cfg.provider == "deepseek":
        try:
            base_url = (cfg.base_url or "https://api.deepseek.com").rstrip("/")
            async with _make_clean_http_client(timeout=30) as client:
                resp = await client.get(
                    f"{base_url}/user/remaining",
                    headers={
                        "Authorization": f"Bearer {cfg.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    total = data.get("data_including_his", {}).get("total_balance", None)
                    used = data.get("data_including_his", {}).get("used_balance", None)
                    remaining = data.get("data_including_his", {}).get("balance_including_his", None)

                    cfg.quota_total = total
                    cfg.quota_used = used
                    cfg.quota_updated_at = datetime.now(timezone.utc)
                    await db.commit()

                    return SuccessResponse(
                        data={
                            "provider": "deepseek",
                            "total_balance": total,
                            "used_balance": used,
                            "remaining_balance": remaining,
                            "raw": data,
                            "updated_at": cfg.quota_updated_at.isoformat() if cfg.quota_updated_at else None,
                        },
                        message="DeepSeek额度查询成功",
                    )
                else:
                    return SuccessResponse(
                        data={
                            "provider": "deepseek",
                            "status": "error",
                            "status_code": resp.status_code,
                            "detail": resp.text[:500],
                        },
                        message="DeepSeek额度查询失败",
                    )
        except Exception as e:
            return SuccessResponse(
                data={"provider": "deepseek", "status": "error", "error": str(e)},
                message=f"DeepSeek额度查询异常: {str(e)}",
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


@router.get("/providers", response_model=SuccessResponse[dict])
async def list_providers(
    current_user: User = Depends(require_admin),
):
    """获取支持的AI提供商列表（含默认Base URL，输入Key即可用）"""
    providers = [
        {
            "id": "deepseek", "name": "DeepSeek",
            "description": "深度求索AI | 高性价比 | 支持思考模式 | 国产开源先锋",
            "base_url": "https://api.deepseek.com", "icon": "🧠",
            "default_model": "deepseek-chat",
        },
        {
            "id": "openai", "name": "OpenAI",
            "description": "GPT系列 | 全球最强多模态 | o1/o3推理模型",
            "base_url": "https://api.openai.com", "icon": "🤖",
            "default_model": "gpt-4o",
        },
        {
            "id": "anthropic", "name": "Anthropic Claude",
            "description": "Claude系列 | 编程/写作顶级 | 安全对齐最强",
            "base_url": "https://api.anthropic.com", "icon": "🎭",
            "default_model": "claude-3-5-sonnet-20241022",
        },
        {
            "id": "google", "name": "Google Gemini",
            "description": "Gemini系列 | 多模态原生支持 | 超长上下文",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "icon": "🌐",
            "default_model": "gemini-2.0-flash",
        },
        {
            "id": "minimax", "name": "MiniMax 海螺AI",
            "description": "国产模型 | ABAB系列 | 高并发低延迟",
            "base_url": "https://api.minimax.chat", "icon": "🎯",
            "default_model": "MiniMax-M2.7",
        },
        {
            "id": "qwen", "name": "阿里通义千问",
            "description": "Qwen系列 | 阿里云旗舰 | 多尺寸可选",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "icon": "☁️",
            "default_model": "qwen-plus",
        },
        {
            "id": "glm", "name": "智谱 ChatGLM",
            "description": "GLM-4系列 | 国产开源标杆 | Flash免费版",
            "base_url": "https://open.bigmodel.cn/api/paas/v4", "icon": "🔮",
            "default_model": "glm-4-flash",
        },
        {
            "id": "moonshot", "name": "月之暗面 Kimi",
            "description": "Moonshot系列 | 超长上下文128K | 国产效率之选",
            "base_url": "https://api.moonshot.cn/v1", "icon": "🌙",
            "default_model": "moonshot-v1-8k",
        },
        {
            "id": "baidu", "name": "百度文心一言",
            "description": "ERNIE系列 | 百度旗舰 | 中文理解领先",
            "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat", "icon": "🐼",
            "default_model": "ernie-4.0-turbo-8k",
        },
        {
            "id": "hunyuan", "name": "腾讯混元",
            "description": "混元系列 | 腾讯旗舰 | Lite免费版可用",
            "base_url": "https://api.hunyuan.cloud.tencent.com/v1", "icon": "🐧",
            "default_model": "hunyuan-lite",
        },
        {
            "id": "spark", "name": "讯飞星火",
            "description": "星火系列 | 讯飞旗舰 | 中文语音领先",
            "base_url": "https://spark-api-open.xf-yun.com/v1", "icon": "⭐",
            "default_model": "generalv3.5",
        },
        {
            "id": "ark", "name": "火山引擎 豆包",
            "description": "豆包系列 | 字节跳动旗舰 | 高性价比",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3", "icon": "🌋",
            "default_model": "doubao-pro-32k",
        },
        {
            "id": "groq", "name": "Groq",
            "description": "Llama/Mixtral系列 | 全球最快推理 | 开源模型托管",
            "base_url": "https://api.groq.com/openai/v1", "icon": "⚡",
            "default_model": "llama-3.3-70b-versatile",
        },
        {
            "id": "custom", "name": "自定义",
            "description": "使用自定义API端点 | 支持任何OpenAI兼容接口",
            "base_url": "", "icon": "⚙️",
            "default_model": "",
        },
    ]
    return SuccessResponse(data={"providers": providers}, message="获取提供商列表成功")


@router.get("/models/{provider}", response_model=SuccessResponse[dict])
async def list_models(
    provider: str,
    current_user: User = Depends(require_admin),
):
    """获取指定提供商支持的模型列表"""
    if provider not in PROVIDER_MODEL_SUGGESTIONS:
        return SuccessResponse(
            data={"provider": provider, "models": []},
            message=f"不支持的提供商: {provider}",
        )
    
    models = PROVIDER_MODEL_SUGGESTIONS[provider]
    return SuccessResponse(
        data={"provider": provider, "models": models},
        message=f"获取{provider}模型列表成功",
    )


@router.get("/models", response_model=SuccessResponse[dict])
async def list_all_models(
    current_user: User = Depends(require_admin),
):
    """获取所有支持的模型列表"""
    return SuccessResponse(
        data={"providers": PROVIDER_MODEL_SUGGESTIONS},
        message="获取所有模型列表成功",
    )
