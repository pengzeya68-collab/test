"""AI Tutor chat / code-review / learning-advice / explain-exercise – migrated from Flask backend/api/ai_tutor.py."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import Exercise, User, AIConfig

router = APIRouter(prefix="/api/v1/ai", tags=["ai-tutor"])

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深的软件测试工程师AI导师，名字叫TestMaster，拥有10年以上的测试行业经验，精通软件测试全栈技术。
你的任务是帮助用户学习软件测试相关知识，解答他们的问题，指导他们提升测试技能。
回答要求：专业且易懂、实用性强、鼓励为主、结构清晰、针对性强。"""

PROMPT_TEMPLATES = {
    "code_review": "用户提交的{language}代码：\n{code}\n\n请审查这段代码，给出：1.语法/逻辑错误 2.优点 3.优化建议 4.优化后代码示例 5.相关知识点",
    "exercise_explain": "用户正在做习题：\n习题标题：{title}\n习题描述：{description}\n用户的答案：{user_answer}\n正确答案：{correct_answer}\n用户回答错误，请详细解释。",
    "learning_advice": "用户当前的技能情况：\n{skill_data}\n\n请给出个性化学习建议。",
}

_conversation_history: dict[int, list[dict]] = {}


def _get_history(user_id: int) -> list[dict]:
    if user_id not in _conversation_history:
        _conversation_history[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return _conversation_history[user_id]


def _trim_history(user_id: int) -> None:
    h = _conversation_history.get(user_id, [])
    if len(h) > 20:
        _conversation_history[user_id] = [h[0]] + h[-18:]


async def _get_active_ai_config(db: AsyncSession) -> Optional[AIConfig]:
    result = await db.execute(select(AIConfig).where(AIConfig.is_active == True))
    return result.scalar_one_or_none()


async def _call_ai_with_config(messages: list[dict], config: AIConfig) -> str:
    import httpx
    from openai import AsyncOpenAI

    http_client = httpx.AsyncClient(
        timeout=config.timeout_seconds,
        trust_env=False,
    )

    try:
        client_kwargs = {"api_key": config.api_key, "http_client": http_client}
        base_url = config.base_url
        if base_url:
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"
            client_kwargs["base_url"] = base_url

        client = AsyncOpenAI(**client_kwargs)

        extra_body = None
        if config.provider == "minimax" and config.group_id:
            extra_body = {"group_id": config.group_id}

        response = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            extra_body=extra_body,
        )

        await client.close()

        if response.choices:
            return response.choices[0].message.content
        raise ValueError("AI返回空响应")
    except Exception:
        try:
            await http_client.aclose()
        except Exception:
            pass
        raise


async def _get_ai_response(messages: list[dict], db: AsyncSession = None) -> str:
    if db is not None:
        config = await _get_active_ai_config(db)
        if config:
            try:
                return await _call_ai_with_config(messages, config)
            except Exception as e:
                logger.error(f"AI调用失败(provider={config.provider}): {e}")

    return _fallback_response(messages)


def _fallback_response(messages: list[dict]) -> str:
    last = ""
    for m in reversed(messages):
        if m["role"] == "user":
            last = m["content"]
            break
    if any(kw in last.lower() for kw in ("python",)):
        return "### Python学习建议\nPython是测试工程师必备语言，建议分阶段学习：基础语法→常用库(requests/pytest/selenium)→框架开发。"
    if "接口测试" in last:
        return "### 接口测试学习指南\n掌握HTTP协议、Postman工具、Python+Requests自动化框架。"
    return "### 测试工程师学习建议\n建议按：测试基础→功能测试→接口/数据库/Linux→自动化测试→性能测试 的路径系统学习。"


@router.post("/chat")
async def ai_chat(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = body.get("question", "")
    context = body.get("context", "")
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    history = _get_history(current_user.id)
    if context:
        history.append({"role": "system", "content": f"上下文信息：{context}"})
    history.append({"role": "user", "content": question})
    _trim_history(current_user.id)

    answer = await _get_ai_response(history, db)
    history.append({"role": "assistant", "content": answer})

    return {"answer": answer, "timestamp": datetime.now().isoformat()}


@router.post("/code-review")
async def code_review(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = body.get("code", "")
    language = body.get("language", "python")
    if not code:
        raise HTTPException(status_code=400, detail="代码不能为空")

    question = PROMPT_TEMPLATES["code_review"].format(language=language, code=code)
    history = _get_history(current_user.id)
    history.append({"role": "user", "content": question})
    _trim_history(current_user.id)

    answer = await _get_ai_response(history, db)
    history.append({"role": "assistant", "content": answer})

    return {"review_result": answer, "timestamp": datetime.now().isoformat()}


@router.get("/learning-advice")
async def learning_advice(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skill_data = {
        "test_theory": 85, "functional_test": 70, "api_test": 50,
        "automation_test": 30, "performance_test": 20, "programming": 65,
        "database": 75, "linux": 60,
    }
    question = PROMPT_TEMPLATES["learning_advice"].format(
        skill_data=json.dumps(skill_data, ensure_ascii=False, indent=2)
    )
    history = _get_history(current_user.id)
    history.append({"role": "user", "content": question})
    _trim_history(current_user.id)

    answer = await _get_ai_response(history, db)
    return {"advice": answer, "skill_data": skill_data, "timestamp": datetime.now().isoformat()}


@router.post("/explain-exercise")
async def explain_exercise(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exercise_id = body.get("exercise_id")
    user_answer = body.get("user_answer", "")
    if not exercise_id:
        raise HTTPException(status_code=400, detail="习题ID不能为空")

    stmt = select(Exercise).where(Exercise.id == exercise_id)
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="习题不存在")

    question = PROMPT_TEMPLATES["exercise_explain"].format(
        title=ex.title, description=ex.description or "",
        user_answer=user_answer, correct_answer=ex.solution or "",
    )
    history = _get_history(current_user.id)
    history.append({"role": "user", "content": question})
    _trim_history(current_user.id)

    answer = await _get_ai_response(history, db)
    return {
        "explanation": answer,
        "exercise_title": ex.title,
        "correct_answer": ex.solution,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/clear-history")
async def clear_history(
    current_user: User = Depends(get_current_user),
):
    if current_user.id in _conversation_history:
        _conversation_history[current_user.id] = [_conversation_history[current_user.id][0]]
    return {"message": "对话历史已清空"}
