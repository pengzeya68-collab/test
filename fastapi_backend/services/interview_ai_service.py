"""
面试 AI 服务
从 routers/interview.py 的 AI 调用逻辑下沉
"""
import logging
import random
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.models import AIConfig, InterviewQuestion

_logger = logging.getLogger(__name__)


async def _get_active_ai_config(db: AsyncSession) -> Optional[AIConfig]:
    result = await db.execute(select(AIConfig).where(AIConfig.is_active == True))
    return result.scalar_one_or_none()


async def _call_openai_chat(
    ai_config: AIConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> Optional[str]:
    import httpx
    from openai import AsyncOpenAI

    http_client = httpx.AsyncClient(timeout=ai_config.timeout_seconds, trust_env=False)
    try:
        client_kwargs = {"api_key": ai_config.api_key, "http_client": http_client}
        base_url = ai_config.base_url
        if base_url:
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"
            client_kwargs["base_url"] = base_url

        client = AsyncOpenAI(**client_kwargs)
        extra_body = None
        if ai_config.provider == "minimax" and ai_config.group_id:
            extra_body = {"group_id": ai_config.group_id}

        response = await client.chat.completions.create(
            model=ai_config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
        )
        await client.close()
        return response.choices[0].message.content.strip() if response.choices else None
    except Exception as e:
        _logger.warning("OpenAI API 调用失败: %s", e)
        return None
    finally:
        try:
            await http_client.aclose()
        except Exception:
            pass


def _extract_follow_up_question(content: str) -> str:
    if not content:
        return ""
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    question_text = ""
    for line in lines:
        if (
            not line.startswith('{')
            and not line.startswith('[')
            and len(line) > 5
            and ('?' in line or '？' in line or '请' in line or '如何' in line or '为什么' in line or '什么' in line or '能否' in line)
        ):
            question_text = line
            break
    if not question_text:
        question_text = lines[0] if lines else content
    question_text = question_text.replace('"', '').replace("'", '').replace('`', '').strip()
    if len(question_text) > 200:
        question_text = question_text[:200]
    return question_text


FALLBACK_FOLLOW_UPS = [
    "能结合实际项目说说你在「{title}」方面的具体实践经验吗？",
    "如果遇到边界情况或异常场景，你会怎么处理？",
    "这个知识点在自动化测试中如何落地应用？",
]


async def generate_follow_up(
    question_title: str,
    user_answer: str,
    ai_feedback: str,
    score: int,
    db: AsyncSession,
) -> Dict[str, str]:
    ai_config = await _get_active_ai_config(db)

    if ai_config:
        prompt = (
            f"你是面试官，候选人刚回答了面试题。\n\n"
            f"题目：{question_title}\n"
            f"候选人的回答：{user_answer}\n"
            f"AI评分：{score}/100\n"
            f"AI已给出的点评摘要：{ai_feedback[:200] if ai_feedback else ''}\n\n"
            f"现在你需要作为面试官，基于候选人的回答提出一个追问。\n\n"
            f"【重要】你只能输出一个追问问题，不要输出任何分析、解释、评价。\n"
            f"追问要求：\n"
            f"- 针对回答中的薄弱点或模糊之处\n"
            f"- 考察更深层次理解\n"
            f"- 与测试开发实际工作场景相关\n"
            f"- 简洁明了，一句话即可\n\n"
            f"直接输出追问内容，不要任何前缀或后缀。"
        )

        content = await _call_openai_chat(
            ai_config,
            system_prompt="你是面试官。用户说什么你就问什么，只输出一个追问问题，不超过50字。",
            user_prompt=prompt,
            temperature=0.9,
            max_tokens=150,
        )

        if content:
            question_text = _extract_follow_up_question(content)
            if question_text:
                return {
                    "follow_up_question": question_text,
                    "follow_up_type": "depth",
                    "hint": "",
                }

    return {
        "follow_up_question": random.choice(FALLBACK_FOLLOW_UPS).format(title=question_title),
        "follow_up_type": "depth",
        "hint": "",
    }


async def generate_reference_answers(
    db: AsyncSession,
    limit: int = 20,
) -> Dict:
    ai_config = await _get_active_ai_config(db)
    if not ai_config:
        return {"error": "请先在AI配置中激活一个大模型"}

    query = select(InterviewQuestion).where(
        (InterviewQuestion.answer.is_(None)) | (InterviewQuestion.answer == "")
    )
    result = await db.execute(query)
    questions = result.scalars().all()

    if not questions:
        return {"total": 0, "generated": 0, "skipped": 0, "remaining": 0, "errors": []}

    target_questions = questions[:limit]
    generated = 0
    skipped = 0
    errors: List[str] = []

    for q in target_questions:
        try:
            desc = q.description or q.content or ""
            prompt = (
                f"你是资深软件测试面试官。请为以下面试题提供一个高质量的参考答案。\n\n"
                f"题目：{q.title}\n"
                f"分类：{q.category or '测试开发'}\n"
                f"难度：{q.difficulty or 'medium'}\n"
                f"题目描述：{desc}\n\n"
                f"参考答案要求：\n"
                f"1. 直接回答问题核心，不要绕弯子\n"
                f"2. 结构清晰，分点作答（用数字序号）\n"
                f"3. 结合实际工作场景举例说明\n"
                f"4. 篇幅适中，200-500字\n"
                f"5. 专业术语准确\n\n"
                f"请直接输出参考答案内容，不要任何前缀或标题。"
            )

            content = await _call_openai_chat(
                ai_config,
                system_prompt="你是资深软件测试面试官，请提供专业、简洁的参考答案。",
                user_prompt=prompt,
                temperature=0.5,
                max_tokens=1000,
            )

            if content and len(content) > 10:
                q.answer = content
                generated += 1
            else:
                skipped += 1

            await db.commit()
            _logger.info("已生成题目 #%d 参考答案", q.id)

        except Exception as e:
            errors.append(f"Q#{q.id}: {str(e)}")
            _logger.error("生成题目 #%d 参考答案失败: %s", q.id, e)
            skipped += 1

    return {
        "total": len(target_questions),
        "generated": generated,
        "skipped": skipped,
        "remaining": max(0, len(questions) - limit),
        "errors": errors[:10],
    }
