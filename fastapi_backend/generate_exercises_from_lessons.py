"""
根据学习路径的课程内容生成习题
- 读取所有学习路径的课程详情（lesson_sections）
- 调用 MiniMax AI 生成习题
- 每个学习路径生成 100+ 道习题
- 习题格式完整（单选题4个选项、多选题4个选项、判断题、代码题）
"""

import asyncio
import json
import logging
import os
import re
from typing import List, Dict, Any

import aiohttp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys

sys.path.insert(0, sys_path)

from fastapi_backend.core.config import settings
from fastapi_backend.models.models import Exercise, LearningPath, LessonSection

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# MiniMax AI 配置
MINIMAX_API_KEY = "sk-cp-PnF3Dqm0wyuV0fd3WL043-IxN00Wuk0H1wvfb_j8-g3BnXbq-CCMSI5SFtZXYfCb7b7qtv4zdvkJtRUGtZLd2QGE2L0CyAbSRk4zQ4F6rkjgpTx-kX9fgI"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "MiniMax-M2.7"
MINIMAX_GROUP_ID = "test_group"


class ExerciseGenerator:
    """根据课程内容生成习题"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stats = {
            "total_paths": 0,
            "total_sections": 0,
            "total_exercises": 0,
            "errors": 0,
        }

    async def generate_exercises_for_all_paths(self):
        """为所有学习路径生成习题"""
        # 获取所有学习路径
        result = await self.db.execute(select(LearningPath).order_by(LearningPath.id))
        paths = result.scalars().all()
        self.stats["total_paths"] = len(paths)

        logger.info(f"📚 找到 {len(paths)} 个学习路径")

        for path in paths:
            await self.generate_exercises_for_path(path)

        logger.info("✅ 完成！总计：")
        logger.info(f"  - 学习路径: {self.stats['total_paths']}")
        logger.info(f"  - 课程章节: {self.stats['total_sections']}")
        logger.info(f"  - 生成习题: {self.stats['total_exercises']}")
        logger.info(f"  - 错误次数: {self.stats['errors']}")

    async def generate_exercises_for_path(self, path: LearningPath):
        """为单个学习路径生成习题"""
        # 获取该路径的所有课程章节
        result = await self.db.execute(
            select(LessonSection).where(LessonSection.learning_path_id == path.id).order_by(LessonSection.sort_order)
        )
        sections = result.scalars().all()

        if not sections:
            logger.warning(f"⚠️  路径 '{path.title}' 没有课程章节，跳过")
            return

        logger.info(f"\n{'=' * 70}")
        logger.info(f"📖 处理路径: {path.title} (ID={path.id})")
        logger.info(f"   课程章节数: {len(sections)}")
        logger.info(f"{'=' * 70}")

        self.stats["total_sections"] += len(sections)

        # 计算需要生成的习题总数（目标100+）
        target_exercises = max(100, len(sections) * 3)  # 每章至少3题
        exercises_per_section = max(2, target_exercises // len(sections))

        logger.info(f"🎯 目标习题数: {target_exercises}")
        logger.info(f"📝 每章生成: {exercises_per_section} 题")

        path_exercises = []

        for section in sections:
            logger.info(f"\n  📄 章节: {section.title[:40]}...")

            # 生成该题的习题
            exercises = await self.generate_exercises_from_section(section, exercises_per_section)

            if exercises:
                path_exercises.extend(exercises)
                logger.info(f"    ✅ 生成 {len(exercises)} 道习题")
            else:
                logger.warning("    ⚠️  未生成习题")

            # 避免API限流
            await asyncio.sleep(0.5)

        # 如果习题不足100道，补充生成
        if len(path_exercises) < 100:
            logger.info("\n  🔄 习题不足100道，补充生成...")
            needed = 100 - len(path_exercises)
            extra_exercises = await self.supplement_exercises(path, sections, needed)
            path_exercises.extend(extra_exercises)

        # 保存到数据库
        logger.info(f"\n  💾 保存 {len(path_exercises)} 道习题到数据库...")
        await self.save_exercises(path.id, path_exercises)

        # 更新学习路径的习题计数
        await self.db.execute(
            update(LearningPath).where(LearningPath.id == path.id).values(exercise_count=len(path_exercises))
        )
        await self.db.commit()

        logger.info(f"  ✅ 路径 '{path.title}' 完成：共 {len(path_exercises)} 道习题")
        self.stats["total_exercises"] += len(path_exercises)

    async def generate_exercises_from_section(self, section: LessonSection, count: int) -> List[Dict[str, Any]]:
        """根据单个课程章节生成习题"""
        # 构建Prompt
        prompt = self._build_prompt(section.content, count)

        # 调用AI
        try:
            ai_response = await self.call_minimax_api(prompt)
            exercises = self.parse_ai_response(ai_response, section)
            return exercises
        except Exception as e:
            logger.error(f"    ❌ 生成失败: {e}")
            self.stats["errors"] += 1
            return []

    def _build_prompt(self, content: str, count: int) -> str:
        """构建AI生成习题的Prompt"""
        # 截断过长的内容（保留前3000字符）
        max_content_length = 3000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[内容已截断...]"

        prompt = f"""你是一个专业的软件测试教育专家。请根据以下课程内容，生成 {count} 道高质量的练习题。

## 课程内容：
{content}

## 要求：
1. 习题必须紧密围绕课程内容，考察重点知识点
2. 题型分配（共{count}题）：
   - 单选题：{int(count * 0.5)}题（必须包含4个选项，A/B/C/D）
   - 多选题：{int(count * 0.2)}题（必须包含4个选项，A/B/C/D）
   - 判断题：{int(count * 0.2)}题
   - 代码题：{int(count * 0.1)}题（如有代码相关内容）
3. 难度分布：简单50%、中等30%、困难20%
4. 每道题必须包含：
   - title: 题目名称（简洁明了）
   - description: 题目描述（包含完整选项，如"A. 选项内容\\nB. 选项内容..."）
   - solution: 正确答案（单选题:A/B/C/D，多选题:AB/ACD等，判断题:true/false）
   - difficulty: 难度（easy/medium/hard）
   - exercise_type: 题型（single_choice/multiple_choice/true_false/code）
   - knowledge_point: 知识点
   - analysis: 答案解析（详细解释为什么）

## 输出格式（严格JSON数组）：
```json
[
  {{
    "title": "题目名称",
    "description": "题目描述\\n\\nA. 选项A\\nB. 选项B\\nC. 选项C\\nD. 选项D",
    "solution": "A",
    "difficulty": "easy",
    "exercise_type": "single_choice",
    "knowledge_point": "知识点名称",
    "analysis": "答案解析..."
  }}
]
```

## 重要：
- 选项必须完整且有区分度，不能有明显错误选项
- 正确答案必须准确，与课程内容一致
- 题目描述中要包含完整选项（A/B/C/D格式）
- 只返回JSON数组，不要其他解释文字
"""
        return prompt

    async def call_minimax_api(self, prompt: str) -> str:
        """调用 MiniMax API"""
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": MINIMAX_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "group_id": MINIMAX_GROUP_ID,
        }

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{MINIMAX_BASE_URL}/chat/completions", headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API调用失败 {response.status}: {error_text}")

                result = await response.json()
                return result["choices"][0]["message"]["content"]

    def parse_ai_response(self, response: str, section: LessonSection) -> List[Dict[str, Any]]:
        """解析AI返回的习题数据"""
        try:
            # 提取JSON（可能包含在```json ```中）
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                response = json_match.group(1)

            # 尝试直接解析
            exercises = json.loads(response)

            if not isinstance(exercises, list):
                raise ValueError("AI返回的不是数组格式")

            # 验证和清洗数据
            valid_exercises = []
            for ex in exercises:
                # 检查必填字段
                if not ex.get("title") or not ex.get("solution"):
                    continue

                # 确保选项格式正确（选择题）
                if ex.get("exercise_type") in ("single_choice", "multiple_choice"):
                    desc = ex.get("description", "")
                    # 检查是否包含选项
                    if "A." not in desc and "A、" not in desc:
                        # 尝试从AI响应中提取选项
                        ex["description"] = self._fix_options(desc, ex.get("exercise_type"))

                valid_exercises.append(ex)

            return valid_exercises

        except json.JSONDecodeError as e:
            logger.error(f"    ❌ JSON解析失败: {e}")
            logger.error(f"    Response: {response[:200]}...")
            raise

    def _fix_options(self, description: str, exercise_type: str) -> str:
        """修复选项格式（如果AI没有生成完整选项）"""
        # 如果description中没有选项，添加默认选项
        if "A." not in description and "A、" not in description:
            # 尝试从title或其他地方提取
            return description + "\n\nA. 选项A\nB. 选项B\nC. 选项C\nD. 选项D"
        return description

    async def supplement_exercises(
        self, path: LearningPath, sections: List[LessonSection], needed: int
    ) -> List[Dict[str, Any]]:
        """补充生成习题（如果不足100道）"""
        logger.info(f"    需要补充 {needed} 道题")

        # 随机选取几个章节，每个章节多生成一些
        import random

        selected_sections = random.sample(sections, min(3, len(sections)))

        extra_exercises = []
        for section in selected_sections:
            count = needed // len(selected_sections) + 1
            exercises = await self.generate_exercises_from_section(section, count)
            extra_exercises.extend(exercises)

            if len(extra_exercises) >= needed:
                break

        return extra_exercises[:needed]

    async def save_exercises(self, path_id: int, exercises: List[Dict[str, Any]]):
        """保存习题到数据库"""
        batch = []
        batch_size = 50

        for ex_data in exercises:
            exercise = Exercise(
                title=ex_data.get("title", "未命名题目"),
                description=ex_data.get("description", ""),
                instructions=ex_data.get("instructions", "请选择正确答案"),
                solution=str(ex_data.get("solution", "")),
                difficulty=ex_data.get("difficulty", "easy"),
                language=ex_data.get("language", "中文"),
                module=ex_data.get("module", "normal"),
                category=ex_data.get("category", ""),
                stage=ex_data.get("stage", 1),
                knowledge_point=ex_data.get("knowledge_point", ""),
                time_estimate=ex_data.get("time_estimate", 1),
            )
            batch.append(exercise)
            self.db.add(exercise)

            if len(batch) >= batch_size:
                await self.db.flush()
                batch = []

        if batch:
            await self.db.flush()

        await self.db.commit()


async def main():
    """主函数"""
    logger.info("🚀 启动习题生成脚本")
    logger.info("=" * 70)

    async with async_session() as session:
        generator = ExerciseGenerator(session)
        await generator.generate_exercises_for_all_paths()

    await engine.dispose()
    logger.info("\n✅ 脚本执行完成！")


if __name__ == "__main__":
    asyncio.run(main())
