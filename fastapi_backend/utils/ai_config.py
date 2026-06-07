"""
共享 AI 配置加载与 LLM 调用工具

供 AITutorService、AITestCaseGenerator 等多个服务复用，避免重复代码。
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

_logger = logging.getLogger(__name__)


@dataclass
class AIParams:
    """AI 调用参数"""

    api_key: str = ""
    base_url: str = ""
    model: str = "gpt-3.5-turbo"
    provider: str = "openai"
    timeout: int = 60
    max_tokens: int = 4000
    temperature: float = 0.3
    group_id: Optional[str] = None


async def load_ai_config(db) -> Optional[object]:
    """
    从数据库加载激活的 AI 配置

    Args:
        db: SQLAlchemy AsyncSession

    Returns:
        AIConfig 对象或 None
    """
    if db is None:
        return None
    from sqlalchemy import select
    from fastapi_backend.models.models import AIConfig

    result = await db.execute(select(AIConfig).where(AIConfig.is_active))
    return result.scalar_one_or_none()


def resolve_ai_params(config=None, defaults: Optional[dict] = None) -> AIParams:
    """
    将 AIConfig 对象解析为 AIParams，无配置时从 settings 回退

    Args:
        config: AIConfig 数据库对象（可为 None）
        defaults: 覆盖默认值的字典（可选）

    Returns:
        AIParams 实例
    """
    from fastapi_backend.core.config import settings
    from fastapi_backend.utils.encryption import decrypt, DecryptionError

    params = AIParams()

    if config:
        try:
            params.api_key = decrypt(config.api_key)
        except (DecryptionError, Exception):
            params.api_key = config.api_key or ""
        params.base_url = config.base_url or ""
        params.model = config.model
        params.provider = (config.provider or "openai").lower()
        params.timeout = config.timeout_seconds or 60
        params.max_tokens = config.max_tokens or 4000
        params.temperature = config.temperature if config.temperature is not None else 0.7
        params.group_id = getattr(config, "group_id", None)
    else:
        params.api_key = getattr(settings, "AI_API_KEY", "") or ""
        params.base_url = getattr(settings, "AI_BASE_URL", "") or ""
        params.model = getattr(settings, "AI_MODEL", "gpt-3.5-turbo")
        params.provider = getattr(settings, "AI_PROVIDER", "openai").lower()
        params.timeout = getattr(settings, "AI_TIMEOUT_SECONDS", 60)
        params.max_tokens = getattr(settings, "AI_MAX_TOKENS", 4000)
        params.temperature = getattr(settings, "AI_TEMPERATURE", 0.7)

    # 仅对 OpenAI 兼容的提供商确保 base_url 以 /v1 结尾
    if params.base_url and params.provider in ("openai", "ark") and not params.base_url.endswith("/v1"):
        params.base_url = params.base_url.rstrip("/") + "/v1"

    # 应用覆盖默认值
    if defaults:
        for k, v in defaults.items():
            if hasattr(params, k) and v is not None:
                setattr(params, k, v)

    return params


async def call_openai_llm(
    params: AIParams,
    messages: list,
    response_format: Optional[dict] = None,
) -> str:
    """
    调用 OpenAI 兼容 LLM，返回原始 content 字符串

    Args:
        params: AI 调用参数
        messages: 消息列表 [{"role": ..., "content": ...}]
        response_format: 响应格式（如 {"type": "json_object"}）

    Returns:
        LLM 返回的 content 字符串

    Raises:
        ValueError: 返回为空时
        Exception: API 调用失败时
    """
    import openai

    http_client = httpx.AsyncClient(timeout=params.timeout, trust_env=False)
    try:
        client_kwargs = {
            "api_key": params.api_key,
            "http_client": http_client,
        }
        if params.base_url:
            client_kwargs["base_url"] = params.base_url

        client = openai.AsyncOpenAI(**client_kwargs)

        create_kwargs = {
            "model": params.model,
            "messages": messages,
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
        }
        if response_format:
            create_kwargs["response_format"] = response_format
        if params.provider == "minimax" and params.group_id:
            create_kwargs["extra_body"] = {"group_id": params.group_id}

        try:
            response = await client.chat.completions.create(**create_kwargs)
        finally:
            await client.close()

        if not response.choices:
            raise ValueError("AI 返回空响应")
        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        if not content:
            # finish_reason='length' 表示输出被 max_tokens 截断
            if finish_reason == "length":
                raise ValueError(
                    f"AI 输出被截断（finish_reason=length, max_tokens={params.max_tokens}），请增大 max_tokens 配置"
                )
            raise ValueError(f"AI 返回内容为空（finish_reason={finish_reason}，可能被安全过滤器拒绝）")
        # 如果输出被截断，记录警告但仍然返回
        if finish_reason == "length":
            _logger.warning(
                "AI 输出可能被截断: finish_reason=length, max_tokens=%d, content_len=%d",
                params.max_tokens,
                len(content),
            )
        return content
    finally:
        try:
            await http_client.aclose()
        except Exception:
            pass


async def call_llm_json(params: AIParams, messages: list) -> dict:
    """
    调用 LLM 并解析 JSON 响应

    Args:
        params: AI 调用参数
        messages: 消息列表

    Returns:
        解析后的 JSON 字典
    """
    content = await call_openai_llm(params, messages, response_format={"type": "json_object"})
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试修复被截断的 JSON
        _logger.warning("JSON 解析失败，尝试修复截断内容 (len=%d)", len(content))
        repaired = _repair_truncated_json(content)
        if repaired is not None:
            return repaired
        raise ValueError(f"AI 返回的 JSON 无法解析: {content[:200]}...")


def _repair_truncated_json(content: str) -> Optional[dict]:
    """尝试修复被截断的 JSON（补全缺失的括号）"""
    # 去除尾部不完整的键值对
    cleaned = content.rstrip()
    # 移除最后一个不完整的键值对（如 "key": "val）→ 回退到上一个逗号
    for _ in range(5):
        try:
            # 尝试补全括号
            open_braces = cleaned.count("{") - cleaned.count("}")
            open_brackets = cleaned.count("[") - cleaned.count("]")
            if open_braces > 0 or open_brackets > 0:
                # 移除最后一个不完整的值
                last_comma = cleaned.rfind(",")
                if last_comma > 0:
                    cleaned = cleaned[:last_comma]
                cleaned += "]" * open_brackets + "}" * open_braces
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            # 继续尝试移除更多内容
            last_comma = cleaned.rfind(",")
            if last_comma > 0:
                cleaned = cleaned[:last_comma]
            else:
                break
    return None
