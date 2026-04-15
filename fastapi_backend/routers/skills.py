"""Skills radar / detail / progress – migrated from Flask backend/api/skills.py."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import Exercise, Progress, User
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.schemas.skills import (
    SkillRadarResponse,
    SkillDetailResponse,
    SkillProgressResponse,
)

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

# ---------------------------------------------------------------------------
# Skill dimension definitions – identical to the Flask version
# ---------------------------------------------------------------------------
SKILL_DIMENSIONS = {
    "test_theory": {
        "name": "测试基础理论",
        "description": "软件测试基础概念、测试方法、测试流程、测试模型等",
        "weight": 0.15,
    },
    "functional_test": {
        "name": "功能测试",
        "description": "Web/APP/小程序功能测试、测试用例设计、缺陷管理等",
        "weight": 0.15,
    },
    "api_test": {
        "name": "接口测试",
        "description": "HTTP协议、接口测试方法、接口自动化、接口测试工具等",
        "weight": 0.15,
    },
    "automation_test": {
        "name": "自动化测试",
        "description": "UI自动化、接口自动化、自动化框架设计、持续集成等",
        "weight": 0.15,
    },
    "performance_test": {
        "name": "性能测试",
        "description": "性能测试方法、性能指标、Jmeter使用、性能调优等",
        "weight": 0.1,
    },
    "programming": {
        "name": "编程能力",
        "description": "Python/Shell等编程语言、数据结构、算法等",
        "weight": 0.1,
    },
    "database": {
        "name": "数据库能力",
        "description": "SQL语法、数据库设计、数据库测试、性能优化等",
        "weight": 0.1,
    },
    "linux": {
        "name": "Linux能力",
        "description": "Linux常用命令、Shell脚本、环境部署、日志排查等",
        "weight": 0.05,
    },
}

SKILL_CATEGORY_MAP = {
    "test_theory": {
        "categories": ["测试基础", "测试用例设计", "功能测试"],
        "languages": ["通用"],
    },
    "functional_test": {
        "categories": ["功能测试", "测试用例设计", "测试基础"],
        "languages": ["通用"],
    },
    "api_test": {
        "categories": ["接口测试"],
        "languages": ["通用"],
        "modules": ["api"],
    },
    "automation_test": {
        "categories": ["自动化测试"],
        "languages": ["Python", "Java"],
        "modules": ["automation"],
    },
    "performance_test": {
        "categories": ["性能测试"],
        "languages": ["通用"],
    },
    "programming": {
        "categories": ["Python编程", "Java编程", "Shell脚本"],
        "languages": ["Python", "Java", "Shell"],
    },
    "database": {
        "categories": ["SQL查询", "数据库"],
        "languages": ["SQL"],
    },
    "linux": {
        "categories": ["Linux命令", "Shell脚本"],
        "languages": ["Linux", "Shell"],
    },
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

INDUSTRY_AVERAGE = [
    {"name": "测试基础理论", "score": 75},
    {"name": "功能测试", "score": 70},
    {"name": "接口测试", "score": 60},
    {"name": "自动化测试", "score": 45},
    {"name": "性能测试", "score": 35},
    {"name": "编程能力", "score": 55},
    {"name": "数据库能力", "score": 65},
    {"name": "Linux能力", "score": 50},
]


def _get_skill_level(score: int) -> str:
    if score >= 90:
        return "专家"
    if score >= 80:
        return "精通"
    if score >= 70:
        return "熟练"
    if score >= 60:
        return "掌握"
    if score >= 40:
        return "了解"
    return "入门"


_SUGGESTIONS: dict[str, dict[str, str]] = {
    "test_theory": {
        "low": "建议先学习软件测试基础概念、测试流程和测试模型，多做测试用例设计练习。",
        "medium": "可以深入学习测试方法论、测试策略制定，尝试参与测试计划编写。",
        "high": "可以研究测试左移、测试右移等先进理念，探索质量体系建设。",
    },
    "functional_test": {
        "low": "多练习Web/APP功能测试，学习测试用例设计方法和缺陷管理流程。",
        "medium": "可以学习专项测试（兼容性、易用性、安全性），提升测试深度。",
        "high": "可以尝试测试流程优化、测试方法创新，提升整体测试效率。",
    },
    "api_test": {
        "low": "先学习HTTP协议基础，掌握Postman等接口测试工具的使用。",
        "medium": "学习接口自动化测试，掌握Requests库和Pytest框架的使用。",
        "high": "可以研究接口自动化框架设计，接入CI/CD流程。",
    },
    "automation_test": {
        "low": "先掌握Python编程基础，学习Selenium/Appium等自动化工具的基本使用。",
        "medium": "学习自动化框架设计，掌握PageObject、数据驱动等设计模式。",
        "high": "可以研究自动化测试平台开发，提升自动化测试覆盖率和稳定性。",
    },
    "performance_test": {
        "low": "先学习性能测试基础概念和指标，掌握Jmeter的基本使用。",
        "medium": "学习性能场景设计、性能监控和瓶颈分析方法。",
        "high": "可以研究全链路压测、性能调优等高级技术。",
    },
    "programming": {
        "low": "从Python基础语法开始学习，多做编程练习题，提升编码能力。",
        "medium": "学习面向对象编程，掌握常用库和框架的使用，多做实战项目。",
        "high": "可以学习数据结构和算法，提升代码质量和性能。",
    },
    "database": {
        "low": "先学习SQL基础语法，掌握常用的增删改查和多表查询。",
        "medium": "学习数据库设计、索引优化、存储过程等高级特性。",
        "high": "可以研究数据库性能优化、分布式数据库等高级技术。",
    },
    "linux": {
        "low": "先学习Linux常用命令，掌握文件操作、进程管理、网络配置等基础操作。",
        "medium": "学习Shell脚本编写，掌握日志排查、环境部署等技能。",
        "high": "可以研究Linux系统优化、自动化运维等高级技术。",
    },
}


def _get_suggestion(skill_key: str, score: int) -> str:
    bucket = _SUGGESTIONS.get(skill_key, {})
    if score < 60:
        return bucket.get("low", "继续加油，多练习就能提升！")
    if score < 80:
        return bucket.get("medium", "继续深入学习，提升技能水平！")
    return bucket.get("high", "已经很优秀了，可以尝试更高难度的挑战！")


async def _calculate_skill_score(
    user_id: int, skill_key: str, db: AsyncSession
) -> int:
    mapping = SKILL_CATEGORY_MAP.get(skill_key, {})
    categories: list[str] = mapping.get("categories", [])
    languages: list[str] = mapping.get("languages", [])
    modules: list[str] = mapping.get("modules", [])

    # Build query for related exercises
    stmt = select(Exercise).where(Exercise.is_public == True)  # noqa: E712
    conditions = []
    if categories:
        conditions.append(Exercise.category.in_(categories))
    if languages:
        conditions.append(Exercise.language.in_(languages))
    if modules:
        conditions.append(Exercise.module.in_(modules))
    if conditions:
        stmt = stmt.where(or_(*conditions))

    result = await db.execute(stmt)
    related_exercises = result.scalars().all()
    total_exercises = len(related_exercises)
    if total_exercises == 0:
        return 0

    exercise_ids = [e.id for e in related_exercises]

    # User progress on these exercises
    prog_stmt = select(Progress).where(
        Progress.user_id == user_id,
        Progress.exercise_id.in_(exercise_ids),
    )
    prog_result = await db.execute(prog_stmt)
    user_progress = prog_result.scalars().all()

    if not user_progress:
        return 0

    completed = [p for p in user_progress if p.completed]
    completion_rate = len(completed) / total_exercises

    scores_with_value = [p.score for p in user_progress if p.score is not None]
    if scores_with_value:
        avg_score_rate = sum(scores_with_value) / (len(scores_with_value) * 100)
    else:
        avg_score_rate = completion_rate

    base_score = completion_rate * 70
    quality_score = avg_score_rate * 30
    total = round(base_score + quality_score)
    return min(total, 100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/radar", response_model=SkillRadarResponse)
async def get_skill_radar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户技能雷达图数据"""
    user_id = current_user.id
    skills_data = []
    total_score = 0.0

    for key, config in SKILL_DIMENSIONS.items():
        score = await _calculate_skill_score(user_id, key, db)
        total_score += score * config["weight"]
        skills_data.append(
            {
                "key": key,
                "name": config["name"],
                "description": config["description"],
                "score": score,
                "level": _get_skill_level(score),
                "suggestion": _get_suggestion(key, score),
                "weight": config["weight"],
            }
        )

    overall_score = round(total_score, 1)
    overall_level = _get_skill_level(overall_score)

    return SkillRadarResponse(
        overall_score=overall_score,
        overall_level=overall_level,
        skills=skills_data,
        industry_average=INDUSTRY_AVERAGE,
        radar_data={
            "indicators": [{"name": s["name"], "max": 100} for s in skills_data],
            "user_data": [s["score"] for s in skills_data],
            "industry_data": [s["score"] for s in INDUSTRY_AVERAGE],
        },
    )


@router.get("/detail/{skill_key}", response_model=SkillDetailResponse)
async def get_skill_detail(
    skill_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个技能的详细信息"""
    if skill_key not in SKILL_DIMENSIONS:
        raise HTTPException(status_code=404, detail="技能不存在")

    user_id = current_user.id
    config = SKILL_DIMENSIONS[skill_key]
    score = await _calculate_skill_score(user_id, skill_key, db)

    # Recommended exercises for this skill
    rec_stmt = (
        select(Exercise)
        .where(Exercise.category == config["name"], Exercise.is_public == True)  # noqa: E712
        .limit(5)
    )
    rec_result = await db.execute(rec_stmt)
    recommended = rec_result.scalars().all()

    exercises = [
        {
            "id": ex.id,
            "title": ex.title,
            "difficulty": ex.difficulty,
            "time_estimate": ex.time_estimate,
        }
        for ex in recommended
    ]

    return SkillDetailResponse(
        key=skill_key,
        name=config["name"],
        description=config["description"],
        score=score,
        level=_get_skill_level(score),
        suggestion=_get_suggestion(skill_key, score),
        recommended_exercises=exercises,
    )


@router.get("/progress", response_model=SkillProgressResponse)
async def get_skill_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取技能提升进度"""
    user_id = current_user.id
    now = datetime.utcnow()
    one_month_ago = now - timedelta(days=30)

    progress_data = []

    for key, config in SKILL_DIMENSIONS.items():
        current_score = await _calculate_skill_score(user_id, key, db)

        # Compute monthly growth
        mapping = SKILL_CATEGORY_MAP.get(key, {})
        categories: list[str] = mapping.get("categories", [])
        languages: list[str] = mapping.get("languages", [])
        modules: list[str] = mapping.get("modules", [])

        ex_stmt = select(Exercise).where(Exercise.is_public == True)  # noqa: E712
        conditions = []
        if categories:
            conditions.append(Exercise.category.in_(categories))
        if languages:
            conditions.append(Exercise.language.in_(languages))
        if modules:
            conditions.append(Exercise.module.in_(modules))
        if conditions:
            ex_stmt = ex_stmt.where(or_(*conditions))

        ex_result = await db.execute(ex_stmt)
        related_exercises = ex_result.scalars().all()
        total_exercises = len(related_exercises)

        monthly_growth = 0
        if total_exercises > 0:
            exercise_ids = [e.id for e in related_exercises]
            recent_stmt = select(func.count()).select_from(Progress).where(
                Progress.user_id == user_id,
                Progress.exercise_id.in_(exercise_ids),
                Progress.completed == True,  # noqa: E712
                Progress.completed_at >= one_month_ago,
            )
            recent_result = await db.execute(recent_stmt)
            recent_completed = recent_result.scalar() or 0
            monthly_growth = round((recent_completed / total_exercises) * 70)

        target = min(current_score + 20, 100)
        if current_score >= 80:
            target = 100

        if current_score > 0 or monthly_growth > 0:
            item: dict = {
                "skill": config["name"],
                "current": current_score,
                "target": target,
                "monthly_growth": monthly_growth,
            }
            remaining = target - current_score
            if monthly_growth > 0 and remaining > 0:
                item["months_needed"] = round(remaining / monthly_growth, 1)
            elif remaining <= 0:
                item["months_needed"] = 0
            else:
                item["months_needed"] = None
            progress_data.append(item)

    # Top 6 by current score, descending
    progress_data.sort(key=lambda x: x["current"], reverse=True)
    progress_data = progress_data[:6]

    return SkillProgressResponse(
        progress=progress_data,
        last_updated=now.strftime("%Y-%m-%d"),
    )


@router.get("/knowledge-map")
async def get_knowledge_map(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取知识点掌握热力图数据"""
    knowledge_points = []

    for key, config in SKILL_DIMENSIONS.items():
        score = await _calculate_skill_score(current_user.id, key, db)
        mapping = SKILL_CATEGORY_MAP.get(key, {})
        categories = mapping.get("categories", [])

        for cat in categories:
            cat_ex_stmt = select(func.count()).select_from(Exercise).where(
                Exercise.category == cat,
                Exercise.is_public == True,  # noqa: E712
            )
            cat_total_result = await db.execute(cat_ex_stmt)
            cat_total = cat_total_result.scalar_one()

            cat_done_stmt = (
                select(func.count())
                .select_from(Progress)
                .join(Exercise, Progress.exercise_id == Exercise.id)
                .where(
                    Progress.user_id == current_user.id,
                    Progress.completed == True,  # noqa: E712
                    Exercise.category == cat,
                )
            )
            cat_done_result = await db.execute(cat_done_stmt)
            cat_done = cat_done_result.scalar_one()

            mastery = round(cat_done / cat_total * 100, 1) if cat_total > 0 else 0

            knowledge_points.append({
                "skill_key": key,
                "skill_name": config["name"],
                "knowledge_point": cat,
                "total_exercises": cat_total,
                "completed_exercises": cat_done,
                "mastery": mastery,
                "score": score,
            })

    knowledge_points.sort(key=lambda x: x["mastery"])

    return {
        "knowledge_points": knowledge_points,
        "total_points": len(knowledge_points),
        "mastered_points": sum(1 for kp in knowledge_points if kp["mastery"] >= 80),
        "learning_points": sum(1 for kp in knowledge_points if 0 < kp["mastery"] < 80),
        "not_started_points": sum(1 for kp in knowledge_points if kp["mastery"] == 0),
    }
