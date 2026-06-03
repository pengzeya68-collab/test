"""
测试项目实战空间路由

路径前缀: /api/v1/projects
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import (
    User,
    LearningPath,
    ProjectSpace,
    ProjectTask,
    ProjectResource,
    ProjectSubmission,
    ProjectEvaluation,
    Progress,
)

router = APIRouter(prefix="/api/v1/projects", tags=["项目实战"])


TASK_TYPE_LABELS = {
    "test_point_design": "测试点设计",
    "test_case_design": "测试用例设计",
    "api_debug": "接口调试",
    "auto_execution": "自动化执行",
    "defect_analysis": "缺陷分析",
    "project_summary": "项目总结",
}

RESOURCE_TYPE_LABELS = {
    "document": "项目文档",
    "api_doc": "接口文档",
    "test_data": "测试数据",
    "reference": "参考资料",
    "link": "外部链接",
}


# ── 统一权限校验 ──


async def _can_access_project(
    project_id: int,
    user: User,
    db: AsyncSession,
) -> bool:
    """
    校验用户是否有权访问指定项目

    规则:
      - Admin 用户: 可访问所有项目
      - 普通用户: 只能访问 is_public=True 的学习路径下、已发布的项目
    """
    if user.is_admin:
        return True

    result = await db.execute(
        select(ProjectSpace).options(selectinload(ProjectSpace.learning_path)).where(ProjectSpace.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        return False

    # 普通用户只能访问 public 学习路径 + 已发布项目
    if project.learning_path and not project.learning_path.is_public:
        return False
    if project.status not in ("published",):
        return False

    return True


async def _get_project_or_404(
    project_id: int,
    user: User,
    db: AsyncSession,
) -> ProjectSpace:
    """
    获取项目并校验访问权限，不存在或无权访问时统一抛出 404。
    返回 ProjectSpace 实例（含 learning_path 预加载）。
    """
    result = await db.execute(
        select(ProjectSpace).options(selectinload(ProjectSpace.learning_path)).where(ProjectSpace.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not user.is_admin:
        if project.learning_path and not project.learning_path.is_public:
            raise HTTPException(status_code=404, detail="项目不存在")
        if project.status not in ("published",):
            raise HTTPException(status_code=404, detail="项目不存在")

    return project


def _fmt_task(task: ProjectTask, submission: Optional[ProjectSubmission] = None) -> dict:
    data = {
        "id": task.id,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "task_type_label": TASK_TYPE_LABELS.get(task.task_type, task.task_type),
        "requirements": task.requirements,
        "hints": task.hints,
        "score": task.score,
        "sort_order": task.sort_order,
        "submission": None,
    }
    if submission:
        data["submission"] = {
            "id": submission.id,
            "content": submission.content,
            "status": submission.status,
            "score": submission.score,
            "feedback": submission.feedback,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        }
    return data


def _fmt_resource(res: ProjectResource) -> dict:
    return {
        "id": res.id,
        "project_id": res.project_id,
        "title": res.title,
        "resource_type": res.resource_type,
        "resource_type_label": RESOURCE_TYPE_LABELS.get(res.resource_type, res.resource_type),
        "content": res.content,
        "url": res.url,
        "sort_order": res.sort_order,
    }


# ── 项目列表（通过 learning_paths 路由提供，这里只做内部辅助） ──


async def _get_user_project_progress(project_id: int, user_id: int, db: AsyncSession) -> dict:
    task_result = await db.execute(select(ProjectTask).where(ProjectTask.project_id == project_id))
    tasks = task_result.scalars().all()
    total = len(tasks)
    if total == 0:
        return {"total_tasks": 0, "completed_tasks": 0, "percent": 0}

    task_ids = [t.id for t in tasks]
    sub_result = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.user_id == user_id,
            ProjectSubmission.task_id.in_(task_ids),
        )
    )
    submissions = sub_result.scalars().all()
    submitted_task_ids = set()
    for s in submissions:
        submitted_task_ids.add(s.task_id)

    completed = len(submitted_task_ids)
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "percent": round(completed / total * 100, 1),
    }


# ── 项目详情 ──


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(ProjectSpace)
        .options(
            selectinload(ProjectSpace.tasks),
            selectinload(ProjectSpace.resources),
            selectinload(ProjectSpace.learning_path),
        )
        .where(ProjectSpace.id == project_id)
    )
    project = result.scalar_one()

    progress_data = await _get_user_project_progress(project_id, current_user.id, db)

    return {
        "id": project.id,
        "learning_path_id": project.learning_path_id,
        "learning_path_title": project.learning_path.title if project.learning_path else "",
        "title": project.title,
        "description": project.description,
        "overview": project.overview,
        "difficulty": project.difficulty,
        "status": project.status,
        "estimated_hours": project.estimated_hours,
        "tasks": [_fmt_task(t) for t in sorted(project.tasks, key=lambda x: x.sort_order)],
        "resources": [_fmt_resource(r) for r in sorted(project.resources, key=lambda x: x.sort_order)],
        "progress": progress_data,
    }


# ── 项目任务列表 ──


@router.get("/{project_id}/tasks")
async def get_project_tasks(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(ProjectSpace).options(selectinload(ProjectSpace.tasks)).where(ProjectSpace.id == project_id)
    )
    project = result.scalar_one()

    tasks = sorted(project.tasks, key=lambda x: x.sort_order)
    task_ids = [t.id for t in tasks]

    sub_result = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.user_id == current_user.id,
            ProjectSubmission.task_id.in_(task_ids),
        )
    )
    submissions_map = {}
    for s in sub_result.scalars().all():
        submissions_map[s.task_id] = s

    return {
        "project_id": project_id,
        "tasks": [_fmt_task(t, submissions_map.get(t.id)) for t in tasks],
    }


# ── 项目资料 ──


@router.get("/{project_id}/resources")
async def get_project_resources(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(ProjectSpace).options(selectinload(ProjectSpace.resources)).where(ProjectSpace.id == project_id)
    )
    project = result.scalar_one()

    return {
        "project_id": project_id,
        "resources": [_fmt_resource(r) for r in sorted(project.resources, key=lambda x: x.sort_order)],
    }


# ── 开始项目 ──


@router.post("/{project_id}/start")
async def start_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, current_user, db)

    sub_check = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.project_id == project_id,
            ProjectSubmission.user_id == current_user.id,
        )
    )
    already_started = sub_check.scalar_one_or_none() is not None

    task_result = await db.execute(select(ProjectTask).where(ProjectTask.project_id == project_id))
    all_tasks = task_result.scalars().all()
    total_tasks = len(all_tasks)
    task_ids = [t.id for t in all_tasks]

    completed = 0
    if task_ids:
        sub_count = await db.execute(
            select(func.count(ProjectSubmission.id)).where(
                ProjectSubmission.project_id == project_id,
                ProjectSubmission.user_id == current_user.id,
                ProjectSubmission.task_id.in_(task_ids),
            )
        )
        completed = sub_count.scalar() or 0

    return {
        "message": "项目已开始，加油！" if not already_started else "项目进行中",
        "project_id": project_id,
        "started": True,
        "progress": {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "percent": round(completed / total_tasks * 100) if total_tasks > 0 else 0,
        },
    }


# ── 项目进度 ──


@router.get("/{project_id}/progress")
async def get_project_progress(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, current_user, db)

    progress_data = await _get_user_project_progress(project_id, current_user.id, db)
    return {
        "project_id": project_id,
        "user_id": current_user.id,
        "progress": progress_data,
    }


# ── 提交任务 ──


@router.post("/{project_id}/tasks/{task_id}/submit")
async def submit_task(
    project_id: int,
    task_id: int,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(ProjectTask).where(ProjectTask.id == task_id, ProjectTask.project_id == project_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    content = body.get("content", "")

    existing = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.user_id == current_user.id,
            ProjectSubmission.task_id == task_id,
        )
    )
    existing_sub = existing.scalar_one_or_none()
    new_sub = None

    if existing_sub:
        existing_sub.content = content
        existing_sub.submitted_at = datetime.now(timezone.utc)
    else:
        new_sub = ProjectSubmission(
            project_id=project_id,
            task_id=task_id,
            user_id=current_user.id,
            content=content,
        )
        db.add(new_sub)

    await db.commit()

    project_result = await db.execute(
        select(ProjectSpace).options(selectinload(ProjectSpace.tasks)).where(ProjectSpace.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    all_task_ids = [t.id for t in project.tasks]
    subs_result = await db.execute(
        select(ProjectSubmission).where(
            ProjectSubmission.user_id == current_user.id,
            ProjectSubmission.task_id.in_(all_task_ids),
        )
    )
    submitted_ids = set(s.task_id for s in subs_result.scalars().all())
    all_submitted = all(tid in submitted_ids for tid in all_task_ids)

    if all_submitted and project.learning_path_id:
        await _update_path_progress(project.learning_path_id, current_user.id, db)

    if all_submitted:
        await _update_user_growth(project, current_user, db)

    active_sub = existing_sub or new_sub
    return {
        "message": "任务提交成功",
        "task_id": task_id,
        "all_submitted": all_submitted,
        "submission": {
            "id": active_sub.id,
            "content": content,
            "status": active_sub.status if hasattr(active_sub, "status") else "pending",
            "submitted_at": (active_sub.submitted_at.isoformat() if active_sub.submitted_at else None)
            if active_sub.submitted_at
            else datetime.now(timezone.utc).isoformat(),
        }
        if active_sub
        else None,
    }


async def _update_path_progress(path_id: int, user_id: int, db: AsyncSession):
    result = await db.execute(
        select(LearningPath).options(selectinload(LearningPath.exercises)).where(LearningPath.id == path_id)
    )
    path = result.scalar_one_or_none()
    if not path:
        return

    for ex in path.exercises:
        prog_result = await db.execute(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.exercise_id == ex.id,
            )
        )
        prog = prog_result.scalar_one_or_none()
        if not prog:
            prog = Progress(
                user_id=user_id,
                exercise_id=ex.id,
                completed=True,
                score=100,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(prog)
        elif not prog.completed:
            prog.completed = True
            prog.completed_at = datetime.now(timezone.utc)

    await db.commit()


async def _update_user_growth(project: ProjectSpace, user: User, db: AsyncSession):
    eval_result = await db.execute(
        select(ProjectEvaluation).where(
            ProjectEvaluation.project_id == project.id,
            ProjectEvaluation.user_id == user.id,
        )
    )
    existing_eval = eval_result.scalar_one_or_none()
    if existing_eval:
        return

    task_scores = sum(t.score for t in project.tasks)
    user.score = (user.score or 0) + task_scores
    user.study_time = (user.study_time or 0) + (project.estimated_hours or 0) * 3600

    total_score = user.score
    if total_score >= 5000:
        user.level = 5
    elif total_score >= 2000:
        user.level = 4
    elif total_score >= 800:
        user.level = 3
    elif total_score >= 200:
        user.level = 2

    evaluation = ProjectEvaluation(
        project_id=project.id,
        user_id=user.id,
        total_score=task_scores,
        is_passed=True,
        comment="恭喜完成项目实战！所有任务已提交。",
        strengths=f"完成{len(project.tasks)}个任务，共{task_scores}分",
    )
    db.add(evaluation)

    await db.commit()


# ── 项目验收/评价 ──


@router.get("/{project_id}/evaluation")
async def get_project_evaluation(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(ProjectEvaluation).where(
            ProjectEvaluation.project_id == project_id,
            ProjectEvaluation.user_id == current_user.id,
        )
    )
    evaluation = result.scalar_one_or_none()

    if not evaluation:
        return {"project_id": project_id, "evaluation": None, "message": "暂无验收评价"}

    return {
        "project_id": project_id,
        "evaluation": {
            "id": evaluation.id,
            "total_score": evaluation.total_score,
            "task_scores": json.loads(evaluation.task_scores) if evaluation.task_scores else {},
            "comment": evaluation.comment,
            "strengths": evaluation.strengths,
            "improvements": evaluation.improvements,
            "is_passed": evaluation.is_passed,
            "evaluated_at": evaluation.evaluated_at.isoformat() if evaluation.evaluated_at else None,
        },
    }


# ── 项目关联的 AutoTest 执行 ──


@router.post("/{project_id}/autotest/run")
async def project_autotest_run(
    project_id: int,
    body: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    body = body or {}
    scenario_id = body.get("scenario_id")
    if not scenario_id:
        raise HTTPException(status_code=400, detail="请提供 scenario_id")

    await _get_project_or_404(project_id, current_user, db)

    from fastapi_backend.core.autotest_database import get_autotest_db
    from fastapi_backend.models.autotest import AutoTestScenario

    async for autotest_db in get_autotest_db():
        scenario_check = await autotest_db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id))
        scenario = scenario_check.scalar_one_or_none()
        if not scenario:
            raise HTTPException(
                status_code=400,
                detail=f"场景(ID={scenario_id})不存在，请确认场景ID有效",
            )

        # 校验场景是否属于该项目
        if scenario.project_id is not None and scenario.project_id != project_id:
            raise HTTPException(
                status_code=403,
                detail=f"场景(ID={scenario_id})不属于该项目(ID={project_id})，请使用项目关联的场景",
            )
        break

    task_check = await db.execute(
        select(ProjectTask).where(
            ProjectTask.project_id == project_id,
            ProjectTask.task_type == "auto_execution",
        )
    )
    task_check.scalars().all()

    from fastapi_backend.services.autotest_scenario_runner import (
        ScenarioExecutionEngine,
    )

    engine = ScenarioExecutionEngine(scenario_id=scenario_id, user_id=current_user.id)
    result = await engine.execute()

    success = result.get("failed_steps", 0) == 0

    if success:
        auto_tasks_result = await db.execute(
            select(ProjectTask).where(
                ProjectTask.project_id == project_id,
                ProjectTask.task_type == "auto_execution",
            )
        )
        for auto_task in auto_tasks_result.scalars().all():
            task_result = await db.execute(
                select(ProjectSubmission).where(
                    ProjectSubmission.user_id == current_user.id,
                    ProjectSubmission.task_id == auto_task.id,
                )
            )
            existing = task_result.scalar_one_or_none()
            if existing:
                existing.content = (
                    f"自动化执行完成: {result.get('total_steps', 0)}步, 成功{result.get('success_steps', 0)}步"
                )
                existing.submitted_at = datetime.now(timezone.utc)
                existing.status = "accepted"
            else:
                sub = ProjectSubmission(
                    project_id=project_id,
                    task_id=auto_task.id,
                    user_id=current_user.id,
                    content=f"自动化执行完成: {result.get('total_steps', 0)}步, 成功{result.get('success_steps', 0)}步",
                    status="accepted",
                )
                db.add(sub)
        await db.commit()

    return {
        "success": success,
        "total_steps": result.get("total_steps", 0),
        "success_steps": result.get("success_steps", 0),
        "failed_steps": result.get("failed_steps", 0),
        "total_time": result.get("total_time", 0),
        "report_url": result.get("report_url"),
    }


# ── 项目关联的考试入口 ──


@router.post("/{project_id}/exam/start")
async def project_exam_start(
    project_id: int,
    body: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exam_id = body.get("exam_id") if body else None
    await _get_project_or_404(project_id, current_user, db)

    if exam_id:
        return {"message": "考试准备就绪", "exam_id": exam_id, "project_id": project_id}

    return {"message": "请指定 exam_id", "project_id": project_id}


# ── 管理接口（已迁移至 admin_paths.py，此处仅保留注释） ──
# 项目创建请使用: POST /api/v1/admin/learning-paths/{path_id}/projects
# 该接口需要 require_admin 权限
