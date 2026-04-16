"""
AI批量生成面试题目脚本
使用已配置的AI自动生成大量实用性面试题
"""
import asyncio
import logging
import random
from typing import Dict, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from fastapi_backend.models.models import AIConfig, InterviewQuestion

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
_logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./instance/testmaster.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


CATEGORIES = [
    ("测试理论", [
        "软件测试的定义和目的", "测试与调试的区别", "测试原则",
        "验证与确认的区别", "质量模型", "测试覆盖度",
        "错误、缺陷、失效的关系", "测试左移和测试右移",
        "测试策略选择", "敏捷测试思维",
    ]),
    ("测试用例设计", [
        "等价类划分法", "边界值分析法", "判定表法",
        "因果图法", "正交试验法", "场景分析法",
        "状态迁移图法", "错误推测法",
    ]),
    ("缺陷管理", [
        "缺陷生命周期", "缺陷严重程度", "缺陷优先级",
        "缺陷报告要素", "缺陷跟踪", "缺陷分类统计",
        "缺陷重现率", "缺陷漏测分析",
    ]),
    ("计算机基础", [
        "HTTP协议原理", "TCP三次握手", "DNS解析过程",
        "Cookie与Session", "RESTful API设计",
        "网页渲染过程", "前端攻击类型", "加密算法基础",
    ]),
    ("Python编程", [
        "Python装饰器", "生成器与迭代器", "列表推导式",
        "多线程与多进程", "Python内存管理", "GIL锁原理",
        "异常处理机制", "上下文管理器", "Python反射机制",
    ]),
    ("Web测试", [
        "表单验证测试", "文件上传测试", "登录功能测试",
        "搜索功能测试", "分页功能测试", "验证码测试",
        "并发测试", "Session/Cookie测试",
    ]),
    ("API测试", [
        "POST与GET区别", "HTTP状态码", "鉴权方式",
        "签名验证", "加密传输", "接口幂等性",
        "批量接口测试", "微服务间通信",
    ]),
    ("自动化测试", [
        "自动化测试策略", "分层测试架构", "PageObject模式",
        "Selenium原理", "等待机制", "PO模式封装",
        "数据驱动测试", "关键字驱动测试", "自动化维护成本",
    ]),
    ("性能测试", [
        "性能指标体系", "响应时间分析", "吞吐量测试",
        "并发用户数", "TPS与QPS", "性能瓶颈定位",
        "缓存命中率", "连接池调优", "JVM调优基础",
    ]),
    ("安全测试", [
        "SQL注入原理", "XSS攻击类型", "CSRF攻击原理",
        "越权访问测试", "敏感信息泄露", "文件上传安全",
        "接口防刷", "验证码安全",
    ]),
    ("Linux", [
        "进程与线程", "磁盘IO排查", "内存泄漏排查",
        "网络诊断命令", "日志分析技巧", "Shell脚本编写",
        "Docker基础", "容器网络",
    ]),
    ("数据库", [
        "SQL查询优化", "索引原理", "事务隔离级别",
        "锁机制", "慢查询分析", "数据库连接池",
        "主从同步", "读写分离", "SQL注入防御",
    ]),
]

DIFFICULTIES = ["easy", "medium", "hard"]
POSITION_LEVELS = ["初级测试工程师", "中级测试工程师", "高级测试工程师"]


async def _get_active_ai_config(session) -> Optional[AIConfig]:
    result = session.execute(select(AIConfig).where(AIConfig.is_active == True))
    return result.scalar_one_or_none()


async def _call_openai_chat(
    ai_config: AIConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 800,
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
        _logger.warning(f"OpenAI API 调用失败: {e}")
        return None
    finally:
        try:
            await http_client.aclose()
        except Exception:
            pass


def _parse_ai_questions(content: str) -> List[Dict]:
    """从AI返回内容解析出多个题目"""
    import re

    questions = []
    lines = content.split('\n')
    current_q = None

    question_pattern = re.compile(r'^(\d+[.、])\s*(.+)')
    answer_starts = ('答', '答案', '参考答案')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测题目开始: "1. 问题..." 或 "Q1: ..."
        match = question_pattern.match(line)
        if match:
            if current_q and current_q.get('title'):
                questions.append(current_q)
            title = match.group(2).strip()
            current_q = {'title': title, 'answer': '', 'difficulty': 'medium'}
        elif current_q is not None:
            # 收集答案内容
            if any(line.startswith(s) for s in answer_starts):
                continue
            if len(line) > 5:
                current_q['answer'] += line + '\n'

    if current_q and current_q.get('title'):
        questions.append(current_q)

    return questions


async def generate_questions_for_category(
    category: str,
    topics: List[str],
    target_count: int,
    ai_config: AIConfig,
    session,
) -> int:
    """为一个分类生成多个题目"""
    generated = 0

    # 每批生成3-5道题
    batch_size = 3
    batches = (target_count + batch_size - 1) // batch_size

    for batch in range(batches):
        remaining = target_count - generated
        if remaining <= 0:
            break

        current_batch = min(batch_size, remaining)
        topic_sample = random.sample(topics, min(3, len(topics)))
        topics_str = '、'.join(topic_sample)

        prompt = f"""你是一名资深软件测试面试官。请为以下话题生成 {current_batch} 道面试题。

话题范围：{topics_str}
分类：{category}

要求：
1. 每道题要实用、具体，考察真实工作能力
2. 避免问概念性问题，多问场景题
3. 难度要多样化，有基础题也有深入题

输出格式：
每道题格式为：序号. 题目内容
题目后换行写参考答案（3-5个要点，用数字分点）

示例格式：
1. 当你发现一个缺陷但开发认为不是缺陷时，你会怎么处理？
参考答案：
1. 首先确认自己的测试环境是否正确
2. 查阅需求文档确认预期行为
3. 提供详细的复现步骤和截图证据
4. 站在用户角度阐述问题的影响
5. 如仍无法达成一致，提请项目经理或产品经理评审

2. ... (下一道题)

直接输出题目，不要有其他说明。"""

        content = await _call_openai_chat(
            ai_config,
            system_prompt="你是资深软件测试面试官，擅长生成高质量、实用性强的面试题。",
            user_prompt=prompt,
            temperature=0.8,
            max_tokens=2000,
        )

        if not content:
            _logger.warning(f"[{category}] AI返回为空，跳过本批")
            await asyncio.sleep(2)
            continue

        questions = _parse_ai_questions(content)
        _logger.info(f"[{category}] 第{batch+1}批生成 {len(questions)} 道题目")

        for q in questions[:remaining]:
            if not q.get('title') or not q.get('answer'):
                continue

            # 检查是否已存在
            existing = session.execute(
                select(InterviewQuestion).where(InterviewQuestion.title == q['title'])
            ).scalar_one_or_none()

            if existing:
                continue

            difficulty = random.choice(DIFFICULTIES)
            position = random.choice(POSITION_LEVELS)

            question = InterviewQuestion(
                title=q['title'][:500],
                category=category,
                difficulty=difficulty,
                position_level=position,
                description="",
                answer=q['answer'][:3000] if q.get('answer') else "",
                tags=f'["{category}"]',
                content="",
                prompt="",
                is_published=True,
            )
            session.add(question)
            generated += 1

        session.commit()
        await asyncio.sleep(1)  # 避免请求过快

    return generated


async def main():
    print("=" * 60)
    print("AI批量生成面试题目")
    print("=" * 60)

    session = Session()

    try:
        ai_config = await _get_active_ai_config(session)
        if not ai_config:
            print("错误: 未找到已激活的AI配置，请先在系统设置中配置并激活AI")
            return

        print(f"使用AI配置: {ai_config.provider} - {ai_config.model}")
        print()

        # 先检查当前数量
        current_count = session.execute(select(InterviewQuestion)).scalar()
        print(f"当前数据库有 {current_count} 道面试题")
        print()

        # 每个分类生成20-30道
        total_target = int(input("请输入每类要生成的题目数量（建议20-30）: ") or "25")
        print(f"将为 {len(CATEGORIES)} 个分类各生成 {total_target} 道题目")
        print(f"预计总题目数: {len(CATEGORIES) * total_target}")
        print()

        confirm = input("确认开始生成？(y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            return

        total_generated = 0

        for category, topics in CATEGORIES:
            print(f"\n{'='*40}")
            print(f"正在生成: {category}")
            print(f"{'='*40}")

            count = await generate_questions_for_category(
                category, topics, total_target, ai_config, session
            )
            total_generated += count
            print(f"[{category}] 完成，新增 {count} 道，当前小计: {total_generated}")

        print()
        print("=" * 60)
        print(f"生成完成！共新增 {total_generated} 道面试题")

        new_total = session.execute(select(InterviewQuestion)).scalar()
        print(f"数据库现有题目总数: {new_total}")
        print("=" * 60)

    finally:
        session.close()


if __name__ == "__main__":
    import sys
    # 支持命令行参数: python batch_generate_questions.py 25
    count_per_category = int(sys.argv[1]) if len(sys.argv) > 1 else 25

    # 直接运行，无需交互
    async def run_batch():
        session = Session()
        try:
            ai_config = await _get_active_ai_config(session)
            if not ai_config:
                print("错误: 未找到已激活的AI配置，请先在系统设置中配置并激活AI")
                return

            print(f"使用AI配置: {ai_config.provider} - {ai_config.model}")

            current_count = session.execute(select(InterviewQuestion)).scalar()
            print(f"当前数据库有 {current_count} 道面试题")
            print(f"将为 {len(CATEGORIES)} 个分类各生成 {count_per_category} 道题目")
            print(f"预计总题目数: {len(CATEGORIES) * count_per_category}")
            print()

            total_generated = 0

            for category, topics in CATEGORIES:
                print(f"\n{'='*40}")
                print(f"正在生成: {category}")
                print(f"{'='*40}")

                count = await generate_questions_for_category(
                    category, topics, count_per_category, ai_config, session
                )
                total_generated += count
                print(f"[{category}] 完成，新增 {count} 道，当前小计: {total_generated}")

            print()
            print("=" * 60)
            print(f"生成完成！共新增 {total_generated} 道面试题")

            new_total = session.execute(select(InterviewQuestion)).scalar()
            print(f"数据库现有题目总数: {new_total}")
            print("=" * 60)

        finally:
            session.close()

    asyncio.run(run_batch())
