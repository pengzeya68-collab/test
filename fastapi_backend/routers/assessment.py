"""Onboarding assessment – quick skill profiling for new users."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import User, LearningPath
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.schemas.assessment import (
    AssessmentQuestion,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    AssessmentStatusResponse,
    DimensionScore,
    RecommendedPath,
)

router = APIRouter(prefix="/api/v1/assessment", tags=["assessment"])

ASSESSMENT_QUESTIONS = [
    {
        "id": 1,
        "dimension": "test_theory",
        "dimension_name": "测试基础理论",
        "question": "以下哪个不属于软件测试的基本原则？",
        "options": [
            "测试能证明缺陷存在，但不能证明缺陷不存在",
            "穷尽测试是不可能的",
            "测试应该由开发人员完成以确保质量",
            "早期的测试活动能节省成本",
        ],
        "correct_index": 2,
        "difficulty": 1,
    },
    {
        "id": 2,
        "dimension": "test_theory",
        "dimension_name": "测试基础理论",
        "question": "等价类划分法的核心思想是什么？",
        "options": [
            "将所有可能的输入随机分组",
            "将输入域划分为若干等价类，从每类中选取代表值",
            "只测试边界值附近的输入",
            "根据代码逻辑设计测试用例",
        ],
        "correct_index": 1,
        "difficulty": 2,
    },
    {
        "id": 3,
        "dimension": "functional_test",
        "dimension_name": "功能测试",
        "question": "在进行 Web 功能测试时，以下哪项是最基本的验证？",
        "options": [
            "页面加载性能是否达标",
            "页面元素和交互是否按需求正常工作",
            "数据库索引是否优化",
            "服务器日志是否正常",
        ],
        "correct_index": 1,
        "difficulty": 1,
    },
    {
        "id": 4,
        "dimension": "functional_test",
        "dimension_name": "功能测试",
        "question": "发现一个 Bug 后，测试人员应该首先做什么？",
        "options": [
            "直接修改代码修复它",
            "记录复现步骤并提交缺陷报告",
            "忽略它，等开发自己发现",
            "在社区发帖讨论",
        ],
        "correct_index": 1,
        "difficulty": 1,
    },
    {
        "id": 5,
        "dimension": "api_test",
        "dimension_name": "接口测试",
        "question": "HTTP 状态码 404 表示什么？",
        "options": [
            "服务器内部错误",
            "请求成功",
            "请求的资源未找到",
            "未授权访问",
        ],
        "correct_index": 2,
        "difficulty": 1,
    },
    {
        "id": 6,
        "dimension": "api_test",
        "dimension_name": "接口测试",
        "question": "在接口测试中，以下哪个方法最适合验证返回数据的结构？",
        "options": [
            "手动查看返回的 JSON",
            "使用 JSON Schema 验证响应结构",
            "只检查状态码是否为 200",
            "截图保存返回结果",
        ],
        "correct_index": 1,
        "difficulty": 2,
    },
    {
        "id": 7,
        "dimension": "automation_test",
        "dimension_name": "自动化测试",
        "question": "以下哪个是 Python 自动化测试框架？",
        "options": [
            "Jenkins",
            "Pytest",
            "Docker",
            "Nginx",
        ],
        "correct_index": 1,
        "difficulty": 1,
    },
    {
        "id": 8,
        "dimension": "automation_test",
        "dimension_name": "自动化测试",
        "question": "数据驱动测试的核心思想是什么？",
        "options": [
            "用 AI 自动生成所有测试用例",
            "将测试数据与测试逻辑分离，通过参数化运行多组数据",
            "只测试数据库相关的功能",
            "手动编写每一条测试数据",
        ],
        "correct_index": 1,
        "difficulty": 2,
    },
    {
        "id": 9,
        "dimension": "programming",
        "dimension_name": "编程能力",
        "question": "Python 中，以下哪个关键字用于定义函数？",
        "options": [
            "function",
            "func",
            "def",
            "define",
        ],
        "correct_index": 2,
        "difficulty": 1,
    },
    {
        "id": 10,
        "dimension": "programming",
        "dimension_name": "编程能力",
        "question": "以下哪种数据结构在 Python 中是不可变的？",
        "options": [
            "list",
            "dict",
            "set",
            "tuple",
        ],
        "correct_index": 3,
        "difficulty": 2,
    },
]

DIMENSION_WEIGHTS = {
    "test_theory": 0.20,
    "functional_test": 0.15,
    "api_test": 0.20,
    "automation_test": 0.20,
    "programming": 0.25,
}

PATH_RECOMMENDATION_MAP = {
    "test_theory": {"priority": 1, "reason": "测试理论基础是你成长的基石，建议优先巩固"},
    "functional_test": {"priority": 2, "reason": "功能测试是日常工作的核心技能，需要系统掌握"},
    "api_test": {"priority": 1, "reason": "接口测试是进阶的必备技能，市场需求大"},
    "automation_test": {"priority": 2, "reason": "自动化能力是薪资突破的关键，建议重点学习"},
    "programming": {"priority": 1, "reason": "编程能力是测试开发的基础，直接影响自动化水平"},
}


def _get_level(score: float) -> str:
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


@router.get("/questions", response_model=list[AssessmentQuestion])
async def get_assessment_questions(
    current_user: User = Depends(get_current_user),
):
    return [
        AssessmentQuestion(
            id=q["id"],
            dimension=q["dimension"],
            dimension_name=q["dimension_name"],
            question=q["question"],
            options=q["options"],
            difficulty=q["difficulty"],
        )
        for q in ASSESSMENT_QUESTIONS
    ]


@router.post("/submit", response_model=AssessmentSubmitResponse)
async def submit_assessment(
    payload: AssessmentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question_map = {q["id"]: q for q in ASSESSMENT_QUESTIONS}

    dimension_scores_raw: dict[str, list[int]] = {}
    for ans in payload.answers:
        q = question_map.get(ans.question_id)
        if not q:
            continue
        dim = q["dimension"]
        if dim not in dimension_scores_raw:
            dimension_scores_raw[dim] = []
        is_correct = 1 if ans.selected_index == q["correct_index"] else 0
        difficulty_bonus = q.get("difficulty", 1) * 0.1
        score = is_correct * (0.7 + difficulty_bonus)
        dimension_scores_raw[dim].append(score)

    dimension_results: list[DimensionScore] = []
    overall_score = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        raw = dimension_scores_raw.get(dim, [])
        if raw:
            avg = sum(raw) / len(raw)
            dim_score = round(avg * 100)
        else:
            dim_score = 0
        overall_score += dim_score * weight
        dimension_results.append(
            DimensionScore(
                key=dim,
                name=ASSESSMENT_QUESTIONS[
                    [i for i, q in enumerate(ASSESSMENT_QUESTIONS) if q["dimension"] == dim][0]
                ]["dimension_name"],
                score=dim_score,
                level=_get_level(dim_score),
            )
        )

    overall_score = round(overall_score, 1)
    overall_level = _get_level(overall_score)

    current_user.score = int(overall_score)
    current_user.level = 1 if overall_score < 40 else 2 if overall_score < 60 else 3 if overall_score < 80 else 4

    stmt = select(LearningPath).where(LearningPath.is_public == True).order_by(LearningPath.id)
    try:
        result = await db.execute(stmt)
        all_paths = result.scalars().all()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"查询学习路径失败: {e}")
        all_paths = []

    sorted_dims = sorted(dimension_results, key=lambda d: d.score)
    recommended = []
    for i, dim in enumerate(sorted_dims[:3]):
        rec_info = PATH_RECOMMENDATION_MAP.get(dim.key, {"priority": 3, "reason": "建议学习提升"})
        matching_paths = [p for p in all_paths if dim.key[:4] in (p.title or "").lower() or dim.name[:2] in (p.title or "")]

        if matching_paths:
            path = matching_paths[0]
        elif all_paths:
            path = all_paths[i % len(all_paths)]
        else:
            continue

        recommended.append(
            RecommendedPath(
                id=path.id,
                title=path.title,
                description=path.description,
                priority=i + 1,
                reason=f"{dim.name}({dim.score}分)较弱 - {rec_info['reason']}",
            )
        )

    try:
        await db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"提交测评结果失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="测评结果保存失败")

    return AssessmentSubmitResponse(
        overall_score=overall_score,
        overall_level=overall_level,
        dimension_scores=dimension_results,
        recommended_paths=recommended,
        has_completed_assessment=True,
    )


@router.get("/status", response_model=AssessmentStatusResponse)
async def get_assessment_status(
    current_user: User = Depends(get_current_user),
):
    has_completed = (current_user.score or 0) > 0
    return AssessmentStatusResponse(
        has_completed_assessment=has_completed,
        overall_score=float(current_user.score) if has_completed else None,
        overall_level=_get_level(current_user.score) if has_completed else None,
    )
