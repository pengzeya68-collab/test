"""JMeter AI 助手路由

路径前缀: /api/ai/jmeter
功能:
1. POST /parameterize - 智能参数化 URL/Body,识别变量并生成 ${var} 引用
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.ai_points import require_ai_points
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User

# 复用 ai_tutor 中的 AI 调用逻辑(数据库中的 AI 配置 + 兜底)
from fastapi_backend.routers.ai_tutor import _get_ai_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/jmeter", tags=["AI-JMeter"])


class ParameterizeRequest(BaseModel):
    """参数化请求"""
    url: str = Field("", description="原始 URL,如 https://api.example.com/users/123")
    method: str = Field("GET", description="HTTP 方法")
    body: str = Field("", description="请求体(JSON 字符串)")
    headers: List[Dict[str, str]] = Field(default_factory=list, description="请求头列表")


class ExtractedVar(BaseModel):
    name: str = Field(..., description="变量名,如 userId")
    source: str = Field("url", description="来源:url/body/header")
    original_value: str = Field(..., description="原始值,如 123")


class SuggestedExtraction(BaseModel):
    varName: str = Field(..., description="建议提取的变量名")
    jsonPath: str = Field(..., description="JSONPath 表达式")
    description: str = Field("", description="说明")


class ParameterizeResponse(BaseModel):
    parameterized_url: str = Field("", description="参数化后的 URL,如 https://${host}/api/users/${userId}")
    parameterized_body: str = Field("", description="参数化后的请求体")
    extracted_vars: List[ExtractedVar] = Field(default_factory=list, description="提取的变量列表")
    suggested_extractions: List[SuggestedExtraction] = Field(default_factory=list, description="建议的响应提取器(用于链式调用)")
    raw_ai_answer: str = Field("", description="AI 原始回答(调试用)")


# 启发式预识别:在调用 AI 之前先用正则识别明显的变量(URL 路径中的数字 ID、查询参数、body 中的字段)
def _heuristic_extract(req: ParameterizeRequest) -> tuple[str, str, List[ExtractedVar]]:
    """返回 (参数化 URL, 参数化 body, 提取的变量列表)"""
    vars_list: List[ExtractedVar] = []
    param_url = req.url
    param_body = req.body

    # URL 路径中的数字 ID: /users/123 -> /users/${userId}
    def _replace_path_id(match: re.Match) -> str:
        val = match.group(1)
        var_name = "userId"
        # 智能命名:根据上下文路径段推断变量名
        prefix = match.string[:match.start()].rstrip("/").split("/")[-1].lower()
        if prefix in ("users", "user", "u"):
            var_name = "userId"
        elif prefix in ("orders", "order", "o"):
            var_name = "orderId"
        elif prefix in ("products", "product", "p"):
            var_name = "productId"
        elif prefix in ("posts", "post"):
            var_name = "postId"
        else:
            var_name = f"{prefix.rstrip('s')}Id" if prefix.endswith("s") else f"{prefix}Id"
        vars_list.append(ExtractedVar(name=var_name, source="url", original_value=val))
        return "/${" + var_name + "}"

    param_url = re.sub(r"/(\d+)(?=/|$|\?)", _replace_path_id, param_url)

    # URL 查询参数中的常量: ?limit=20 -> ?limit=${limit}
    if "?" in param_url:
        base, qs = param_url.split("?", 1)
        for kv in qs.split("&"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                if v and not v.startswith("${"):
                    var_name = k
                    vars_list.append(ExtractedVar(name=var_name, source="url", original_value=v))
                    param_url = param_url.replace(f"{k}={v}", f"{k}=${{{var_name}}}")

    # body 中的 ID 字段
    if param_body and param_body.strip().startswith("{"):
        try:
            body_obj = json.loads(param_body)
            modified = False
            for k, v in list(body_obj.items()):
                if isinstance(v, (int, str)) and re.fullmatch(r"\d+", str(v)):
                    var_name = k
                    vars_list.append(ExtractedVar(name=var_name, source="body", original_value=str(v)))
                    body_obj[k] = "${" + var_name + "}"
                    modified = True
            if modified:
                param_body = json.dumps(body_obj, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            pass

    return param_url, param_body, vars_list


PARAMETERIZE_PROMPT_TEMPLATE = """你是 JMeter 性能测试专家。请分析以下 HTTP 请求并完成参数化:

请求方法: {method}
原始 URL: {url}
请求体: {body}
请求头: {headers}

已知启发式提取的变量: {heuristic_vars}

任务:
1. 识别 URL/Body 中应该参数化的常量(用户 ID、订单 ID、时间戳、token 等)
2. 为每个变量建议合理的变量名(驼峰命名,如 userId、orderId、timestamp)
3. 输出参数化后的 URL 和 Body(用 ${{varName}} 标记变量)
4. 如果 Body 是 JSON,建议从响应中提取这些变量的 JSONPath 表达式(用于链式调用)

请用 JSON 格式回复,字段如下:
{{
  "parameterized_url": "参数化后的 URL",
  "parameterized_body": "参数化后的 Body(原样返回如果无需参数化)",
  "extracted_vars": [{{"name": "变量名", "source": "url|body|header", "original_value": "原值"}}],
  "suggested_extractions": [{{"varName": "变量名", "jsonPath": "$.data.id", "description": "说明"}}]
}}

只输出 JSON,不要其他解释。"""


@router.post("/parameterize", response_model=ParameterizeResponse)
async def jmeter_parameterize(
    req: ParameterizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _ai=Depends(require_ai_points("ai_jmeter_parameterize")),
):
    """AI 智能参数化 JMeter 请求

    分析 URL/Body 中的常量,生成 ${var} 引用,并建议响应提取器(用于链式调用)。
    """
    # 1. 先用启发式规则预识别明显变量
    h_url, h_body, h_vars = _heuristic_extract(req)

    # 2. 调用 AI 进行深度分析(识别语义变量名 + 建议提取器)
    prompt = PARAMETERIZE_PROMPT_TEMPLATE.format(
        method=req.method,
        url=req.url or "(空)",
        body=req.body or "(空)",
        headers=json.dumps(req.headers, ensure_ascii=False) if req.headers else "(空)",
        heuristic_vars=json.dumps([v.model_dump() for v in h_vars], ensure_ascii=False) if h_vars else "(无)",
    )

    messages = [
        {"role": "system", "content": "你是 JMeter 性能测试专家,擅长参数化测试脚本。"},
        {"role": "user", "content": prompt},
    ]

    try:
        answer = await _get_ai_response(messages, db)
    except Exception as e:
        logger.error("AI 参数化调用失败: %s", e)
        await db.rollback()
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败: {e}")

    await _ai()

    # 3. 解析 AI 回答(容错:提取 JSON 片段)
    result = _parse_ai_answer(answer)

    # 4. 如果 AI 没有识别到变量,用启发式结果兜底
    if not result.get("extracted_vars") and h_vars:
        result["extracted_vars"] = [v.model_dump() for v in h_vars]
    if not result.get("parameterized_url") and h_url:
        result["parameterized_url"] = h_url
    if not result.get("parameterized_body") and h_body:
        result["parameterized_body"] = h_body

    result["raw_ai_answer"] = answer
    return ParameterizeResponse(**result)


def _parse_ai_answer(answer: str) -> dict:
    """从 AI 回答中提取 JSON 结果(容错处理)"""
    if not answer:
        return {}

    # 尝试提取 ```json ... ``` 代码块
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", answer)
    if m:
        answer = m.group(1)

    # 直接解析
    try:
        return json.loads(answer)
    except (json.JSONDecodeError, ValueError):
        pass

    # 提取第一个 {... } 块
    start = answer.find("{")
    end = answer.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(answer[start:end + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    return {}
