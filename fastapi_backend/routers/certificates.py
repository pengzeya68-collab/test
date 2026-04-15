"""技能证书路由 - 学习成果认证"""
from __future__ import annotations

import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Progress, ExerciseSubmissionRecord

router = APIRouter(prefix="/api/v1/certificates", tags=["技能证书"])

CERTIFICATE_LEVELS = {
    "test_beginner": {
        "name": "测试入门认证",
        "description": "完成测试基础理论相关习题，掌握软件测试核心概念",
        "icon": "🔰",
        "required_score": 40,
        "skill_key": "test_theory",
        "level": "初级",
    },
    "functional_tester": {
        "name": "功能测试专员",
        "description": "精通功能测试方法，能独立设计测试用例和执行测试",
        "icon": "📋",
        "required_score": 50,
        "skill_key": "functional_test",
        "level": "中级",
    },
    "api_tester": {
        "name": "接口测试工程师",
        "description": "掌握接口测试方法，能使用工具进行接口自动化测试",
        "icon": "🔌",
        "required_score": 50,
        "skill_key": "api_test",
        "level": "中级",
    },
    "automation_engineer": {
        "name": "自动化测试工程师",
        "description": "精通自动化测试框架设计和持续集成实践",
        "icon": "🤖",
        "required_score": 60,
        "skill_key": "automation_test",
        "level": "高级",
    },
    "performance_tester": {
        "name": "性能测试专家",
        "description": "掌握性能测试方法和性能调优技术",
        "icon": "⚡",
        "required_score": 50,
        "skill_key": "performance_test",
        "level": "高级",
    },
    "programming_expert": {
        "name": "编程能力认证",
        "description": "具备扎实的编程基础，能编写高质量测试脚本",
        "icon": "💻",
        "required_score": 50,
        "skill_key": "programming",
        "level": "中级",
    },
    "database_expert": {
        "name": "数据库能力认证",
        "description": "精通SQL查询和数据库测试方法",
        "icon": "🗄️",
        "required_score": 50,
        "skill_key": "database",
        "level": "中级",
    },
    "linux_expert": {
        "name": "Linux能力认证",
        "description": "掌握Linux常用命令和Shell脚本编写",
        "icon": "🐧",
        "required_score": 40,
        "skill_key": "linux",
        "level": "中级",
    },
    "all_rounder": {
        "name": "全能测试专家",
        "description": "所有技能维度均达到较高水平，具备全面的测试能力",
        "icon": "🌟",
        "required_score": 60,
        "skill_key": None,
        "level": "专家",
    },
}


def _generate_cert_id(user_id: int, cert_key: str) -> str:
    raw = f"cert-{user_id}-{cert_key}-{datetime.utcnow().strftime('%Y%m%d')}"
    return hashlib.md5(raw.encode()).hexdigest()[:12].upper()


@router.get("/")
async def get_certificates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的证书列表（含未解锁的）"""
    from fastapi_backend.routers.skills import _calculate_skill_score, SKILL_DIMENSIONS

    skill_scores = {}
    for key in SKILL_DIMENSIONS:
        skill_scores[key] = await _calculate_skill_score(current_user.id, key, db)

    total_stmt = select(func.count()).select_from(Progress).where(
        Progress.user_id == current_user.id,
        Progress.completed == True,  # noqa: E712
    )
    total_result = await db.execute(total_stmt)
    total_completed = total_result.scalar_one()

    certificates = []
    for key, config in CERTIFICATE_LEVELS.items():
        if config["skill_key"]:
            score = skill_scores.get(config["skill_key"], 0)
        else:
            all_scores = list(skill_scores.values())
            score = sum(all_scores) / len(all_scores) if all_scores else 0

        unlocked = score >= config["required_score"]
        cert_id = _generate_cert_id(current_user.id, key) if unlocked else None

        certificates.append({
            "key": key,
            "name": config["name"],
            "description": config["description"],
            "icon": config["icon"],
            "level": config["level"],
            "required_score": config["required_score"],
            "current_score": round(score, 1),
            "unlocked": unlocked,
            "cert_id": cert_id,
            "issued_at": datetime.utcnow().strftime("%Y-%m-%d") if unlocked else None,
        })

    unlocked_count = sum(1 for c in certificates if c["unlocked"])

    return {
        "certificates": certificates,
        "unlocked_count": unlocked_count,
        "total_count": len(certificates),
        "username": current_user.username,
        "overall_score": current_user.score or 0,
    }
