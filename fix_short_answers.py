"""
修复面试题答案过短问题
使用AI重新生成短答案
"""
import asyncio
import logging
import sys
import re

from sqlalchemy import create_engine, select, func, and_
from sqlalchemy.orm import sessionmaker
from fastapi_backend.models.models import AIConfig, InterviewQuestion

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
_logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./instance/testmaster.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


async def _get_active_ai_config(session) -> AIConfig:
    result = session.execute(select(AIConfig).where(AIConfig.is_active == True))
    return result.scalar_one_or_none()


async def _call_openai_chat(
    ai_config: AIConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> str:
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
        return response.choices[0].message.content.strip() if response.choices else ""
    except Exception as e:
        _logger.warning(f"OpenAI API 调用失败: {e}")
        return ""
    finally:
        try:
            await http_client.aclose()
        except Exception:
            pass


async def fix_short_answers():
    session = Session()

    try:
        ai_config = await _get_active_ai_config(session)
        if not ai_config:
            print("错误: 未找到已激活的AI配置")
            return

        print(f"使用AI配置: {ai_config.provider} - {ai_config.model}")

        # 找出答案过短的题目
        short_questions = session.execute(
            select(InterviewQuestion).where(
                and_(
                    InterviewQuestion.answer != None,
                    func.length(InterviewQuestion.answer) < 50
                )
            )
        ).scalars().all()

        print(f"找到 {len(short_questions)} 道答案过短的题目")

        if not short_questions:
            print("没有需要修复的题目")
            return

        # 确认
        confirm = input(f"确认开始修复？(y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            return

        fixed = 0
        failed = 0

        for idx, q in enumerate(short_questions):
            print(f"\n[{idx+1}/{len(short_questions)}] 修复: {q.title[:40]}...")

            difficulty_map = {"easy": "简单", "medium": "中等", "hard": "困难"}
            diff_text = difficulty_map.get(q.difficulty, "中等")

            prompt = f"""题目：{q.title}
分类：{q.category or '测试开发'}
难度：{diff_text}

请为这道面试题提供一个高质量的参考答案。要求：
1. 直接回答问题核心，不要绕弯子
2. 结构清晰，分点作答（用数字序号）
3. 结合实际工作场景举例说明
4. 篇幅适中，100-300字
5. 专业术语准确

直接输出参考答案内容，不要任何前缀。"""

            answer = await _call_openai_chat(
                ai_config,
                system_prompt="你是资深软件测试面试官，请提供专业、简洁、有实际价值的参考答案。",
                user_prompt=prompt,
                temperature=0.7,
                max_tokens=500,
            )

            if answer and len(answer) > 30:
                q.answer = answer
                session.commit()
                fixed += 1
                print(f"  [OK] 答案已更新 ({len(answer)}字)")
            else:
                failed += 1
                print(f"  [FAIL] AI返回无效")

            await asyncio.sleep(1.5)  # 避免请求过快

        print("\n" + "=" * 50)
        print(f"修复完成！成功: {fixed}, 失败: {failed}")
        print("=" * 50)

    finally:
        session.close()


if __name__ == "__main__":
    import sys
    auto_confirm = len(sys.argv) > 1 and sys.argv[1] == '--yes'

    async def run_with_confirm():
        session = Session()
        try:
            ai_config = await _get_active_ai_config(session)
            if not ai_config:
                print("错误: 未找到已激活的AI配置")
                return

            print(f"使用AI配置: {ai_config.provider} - {ai_config.model}")

            short_questions = session.execute(
                select(InterviewQuestion).where(
                    and_(InterviewQuestion.answer != None, func.length(InterviewQuestion.answer) < 50)
                )
            ).scalars().all()

            print(f"找到 {len(short_questions)} 道答案过短的题目")

            if not short_questions:
                print("没有需要修复的题目")
                return

            if not auto_confirm:
                confirm = input(f"确认开始修复？(y/n): ")
                if confirm.lower() != 'y':
                    print("已取消")
                    return

            fixed = 0
            failed = 0

            for idx, q in enumerate(short_questions):
                print(f"\n[{idx+1}/{len(short_questions)}] 修复: {q.title[:40]}...")

                difficulty_map = {"easy": "简单", "medium": "中等", "hard": "困难"}
                diff_text = difficulty_map.get(q.difficulty, "中等")

                prompt = f"""题目：{q.title}
分类：{q.category or '测试开发'}
难度：{diff_text}

请为这道面试题提供一个高质量的参考答案。要求：
1. 直接回答问题核心，不要绕弯子
2. 结构清晰，分点作答（用数字序号）
3. 结合实际工作场景举例说明
4. 篇幅适中，100-300字
5. 专业术语准确

直接输出参考答案内容，不要任何前缀。"""

                answer = await _call_openai_chat(
                    ai_config,
                    system_prompt="你是资深软件测试面试官，请提供专业、简洁、有实际价值的参考答案。",
                    user_prompt=prompt,
                    temperature=0.7,
                    max_tokens=500,
                )

                if answer and len(answer) > 30:
                    q.answer = answer
                    session.commit()
                    fixed += 1
                    print(f"  [OK] 答案已更新 ({len(answer)}字)")
                else:
                    failed += 1
                    print(f"  [FAIL] AI返回无效")

                await asyncio.sleep(1.5)

            print("\n" + "=" * 50)
            print(f"修复完成！成功: {fixed}, 失败: {failed}")
            print("=" * 50)

        finally:
            session.close()

    asyncio.run(run_with_confirm())
