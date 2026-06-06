from typing import Optional
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import NotFoundException
from fastapi_backend.deps.auth import get_current_active_user, require_admin
from fastapi_backend.models.models import (
    InterviewQuestion,
    InterviewSession,
    Submission,
    User,
    Exercise,
)
from fastapi_backend.schemas.common import SuccessResponse, PaginationResponse
from fastapi_backend.schemas.interview import (
    CodeSubmission,
    AIEvaluationResponse,
    UserInterviewStatistics,
)
from fastapi_backend.schemas.interview_question import (
    InterviewQuestionDetail,
    InterviewQuestionList,
    InterviewQuestionListResponse,
)
from fastapi_backend.schemas.interview_session import (
    InterviewSessionCreate,
    InterviewSessionDetail,
    InterviewSessionWithQuestion,
)
from fastapi_backend.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionResultDetail,
    SubmissionHistoryItem,
)
from fastapi_backend.services.ai_tutor_service import AITutorService
from fastapi_backend.services.interview_execution_service import (
    interview_execution_service,
)
from fastapi_backend.services.interview_stats_service import (
    get_user_interview_statistics,
    generate_interview_report,
    complete_session,
    get_interview_history,
    get_submission_result_detail,
)
from fastapi_backend.deps.ai_points import require_ai_points
from fastapi_backend.services.interview_ai_service import (
    generate_follow_up,
    generate_reference_answers,
)

router = APIRouter(prefix="/api/v1/interview", tags=["AI 模拟面试"])


@router.post("/evaluate", response_model=SuccessResponse[AIEvaluationResponse])
async def evaluate_interview_code(submission: CodeSubmission, tutor: AITutorService = Depends(AITutorService), db: AsyncSession = Depends(get_db), _ai=Depends(require_ai_points("interview_code_eval"))):
    try:
        result = await tutor.evaluate_code(submission)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=502, detail="AI 服务调用失败，积分已退还")
    await _ai()
    return SuccessResponse(data=result, message="代码评估完成")


@router.get("/questions", response_model=SuccessResponse[InterviewQuestionListResponse])
async def list_interview_questions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（标题、描述、标签）"),
    difficulty: Optional[str] = Query(None, description="难度筛选: easy/medium/hard"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试题目列表，支持分页、搜索、筛选
    普通用户只能看到已发布的题目，管理员可以看到所有题目
    """
    # 构建基础查询
    query = select(InterviewQuestion)

    # 根据用户角色过滤发布状态
    if not current_user.is_admin:
        query = query.where(InterviewQuestion.is_published)

    # 关键词搜索
    if keyword:
        keyword_filter = or_(
            InterviewQuestion.title.contains(keyword),
            InterviewQuestion.description.contains(keyword),
            InterviewQuestion.tags.contains(keyword),
        )
        query = query.where(keyword_filter)

    # 难度筛选
    if difficulty and difficulty.lower() in ["easy", "medium", "hard"]:
        query = query.where(InterviewQuestion.difficulty == difficulty.lower())

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 计算分页
    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    # 执行查询
    query = query.order_by(InterviewQuestion.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    questions = result.scalars().all()

    # 转换为列表项
    items = [InterviewQuestionList.model_validate(q) for q in questions]

    # 构建响应
    list_response = InterviewQuestionListResponse(items=items, total=total, page=page, size=size, pages=pages)

    return SuccessResponse(data=list_response, message=f"获取到 {len(items)} 道题目")


@router.get("/questions/{question_id}", response_model=SuccessResponse[InterviewQuestionDetail])
async def get_interview_question(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试题目详情
    普通用户只能查看已发布的题目，管理员可以查看所有题目
    """
    query = select(InterviewQuestion).where(InterviewQuestion.id == question_id)

    # 普通用户只能查看已发布的题目
    if not current_user.is_admin:
        query = query.where(InterviewQuestion.is_published)

    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在或您没有权限查看")

    return SuccessResponse(
        data=InterviewQuestionDetail.model_validate(question),
        message="题目详情获取成功",
    )


@router.post(
    "/sessions",
    response_model=SuccessResponse[InterviewSessionDetail],
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_session(
    session_data: InterviewSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的面试会话
    用户点击"开始面试"时调用，为指定题目创建新的会话
    """
    # 验证题目是否存在且已发布（对普通用户）
    question_query = select(InterviewQuestion).where(InterviewQuestion.id == session_data.question_id)
    if not current_user.is_admin:
        question_query = question_query.where(InterviewQuestion.is_published)

    question_result = await db.execute(question_query)
    question = question_result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在或您没有权限访问")

    # 检查是否已有进行中的会话
    active_session_query = select(InterviewSession).where(
        InterviewSession.user_id == current_user.id,
        InterviewSession.question_id == session_data.question_id,
        InterviewSession.status.in_(["started", "submitted"]),
    )
    active_result = await db.execute(active_session_query)
    active_session = active_result.scalar_one_or_none()

    if active_session:
        # 返回已存在的进行中会话
        return SuccessResponse(
            data=InterviewSessionDetail.model_validate(active_session),
            message="已存在进行中的会话，继续使用该会话",
        )

    # 创建新会话
    new_session = InterviewSession(user_id=current_user.id, question_id=session_data.question_id, status="started")

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return SuccessResponse(
        data=InterviewSessionDetail.model_validate(new_session),
        message="面试会话创建成功",
    )


class BatchSessionCreate(BaseModel):
    """批量创建面试会话"""

    position: str = Field(default="测试工程师", description="目标岗位")
    level: str = Field(default="中级", description="难度级别")
    type: str = Field(default="技术面", description="面试类型")
    question_count: int = Field(default=10, ge=1, le=50, description="题目数量")
    categories: list[str] = Field(default_factory=list, description="考察范围分类")


@router.post(
    "/sessions/batch",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
async def create_batch_interview_session(
    body: BatchSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    import random

    difficulty_map = {"初级": "easy", "中级": "medium", "高级": "hard", "专家": "hard"}
    difficulty = difficulty_map.get(body.level, None)

    # 前端大类 → Exercise 表细分类映射
    exercise_category_map = {
        "测试基础": [
            "测试基础", "软件测试的定义与目的", "软件开发生命周期与测试模型",
            "测试分类体系", "测试的七大原则", "计算机硬件基础", "操作系统基础",
            "网络基础",
        ],
        "测试用例设计": [
            "测试用例设计", "等价类划分", "边界值分析", "决策表测试",
            "正交实验设计", "测试用例设计概述", "接口测试用例设计", "AI用例生成",
        ],
        "缺陷管理": [
            "缺陷管理", "缺陷基础概念", "缺陷报告编写", "缺陷管理流程",
            "缺陷管理工具", "缺陷预防与过程改进", "缺陷管理与追踪",
            "缺陷分析与RCA", "ML缺陷预测",
        ],
        "功能测试": [
            "功能测试", "兼容性测试", "弱网测试",
        ],
        "Web测试": [
            "Web测试", "Web安全概述",
        ],
        "接口测试": [
            "接口测试", "HTTP协议基础", "接口测试概述", "常用接口测试工具",
            "Requests库基础", "接口自动化测试", "接口自动化测试实战",
            "RESTful API开发",
        ],
        "自动化测试": [
            "自动化测试", "Pytest框架基础", "测试框架集成",
            "自愈自动化测试", "视觉回归测试",
        ],
        "UI自动化": [
            "UI自动化", "Selenium概述", "元素定位", "等待机制",
        ],
        "性能测试": [
            "性能测试", "性能测试核心指标", "JMeter基础", "JMeter脚本开发",
            "JMeter分布式", "Locust开发", "性能监控", "性能调优",
        ],
        "安全测试": [
            "安全测试", "网络安全基础", "Web安全概述", "SQL注入", "XSS攻击",
            "CSRF/SSRF", "认证授权安全", "安全编码与DevSecOps",
            "Burp Suite工具", "文件上传漏洞",
        ],
        "数据库": [
            "数据库", "SQL基础概念", "SELECT查询基础", "表连接（JOIN）",
            "聚合函数与分组", "数据操作", "数据库设计与ORM",
        ],
        "Linux": [
            "Linux", "文件与目录操作", "文件权限管理", "进程管理",
            "系统管理", "网络管理", "常用操作",
        ],
        "Python编程": [
            "Python编程", "Python基础概念", "变量与数据类型", "控制流",
            "函数与模块", "面向对象编程",
        ],
        "移动端测试": [
            "移动端测试", "移动端测试概述", "移动端功能测试", "Appium自动化",
        ],
        "CI/CD": [
            "CI/CD", "CI/CD概念", "Docker容器化", "Git工作流",
            "GitLab CI/CD", "Jenkins Pipeline",
        ],
        "测试策略": [
            "测试策略", "测试架构师概述", "分层测试体系", "可测试性设计",
            "微服务测试", "质量度量模型", "质量门禁",
        ],
        "测试开发": [
            "测试开发", "需求分析与技术选型", "前端页面开发", "测试执行引擎",
            "测试报表与可视化", "定时任务与通知", "平台部署",
        ],
        "测试管理": [
            "测试管理", "测试计划概述", "测试计划的内容", "测试进度与里程碑",
            "测试团队管理", "测试团队与工具链", "测试风险管理", "TMMi成熟度模型",
        ],
        "AI测试": [
            "AI测试", "AI测试概述", "LLM测试生成", "NLP测试应用",
        ],
    }

    selected = []
    source_type = None

    query = select(Exercise).where(Exercise.is_public)
    if body.categories:
        all_mapped = []
        for c in body.categories:
            if c in exercise_category_map:
                all_mapped.extend(exercise_category_map[c])
            else:
                all_mapped.append(c)
        if all_mapped:
            query = query.where(Exercise.category.in_(all_mapped) | Exercise.knowledge_point.in_(all_mapped))
    if difficulty:
        query = query.where(Exercise.difficulty == difficulty)

    result = await db.execute(query)
    exercises = result.scalars().all()

    if exercises:
        selected_exercises = random.sample(exercises, min(body.question_count, len(exercises)))
        for ex in selected_exercises:
            selected.append(
                {
                    "id": ex.id,
                    "title": ex.title,
                    "category": ex.category or "",
                    "difficulty": ex.difficulty or "medium",
                    "content": ex.description or ex.instructions or "",
                    "template_code": ex.code_template or "",
                    "answer": ex.solution or ex.expected_output or "",
                    "language": ex.exercise_type or ("text" if not ex.code_template else "python"),
                    "is_answered": False,
                    "user_answer": "",
                    "score": None,
                    "ai_feedback": None,
                    "parsed_feedback": None,
                    "record_id": None,
                    "_source": "exercise",
                }
            )
        source_type = "exercise"

    if len(selected) < body.question_count:
        remaining = body.question_count - len(selected)
        iq_query = select(InterviewQuestion).where(InterviewQuestion.is_published)
        if body.categories:
            valid_cats = [c for c in body.categories if c != "其他"]
            if valid_cats:
                iq_query = iq_query.where(InterviewQuestion.category.in_(valid_cats))
        if difficulty:
            iq_query = iq_query.where(InterviewQuestion.difficulty == difficulty)
        existing_ids = {s["id"] for s in selected}
        iq_result = await db.execute(iq_query)
        iq_questions = [q for q in iq_result.scalars().all() if q.id not in existing_ids]

        if iq_questions:
            extra = random.sample(iq_questions, min(remaining, len(iq_questions)))
            for q in extra:
                selected.append(
                    {
                        "id": q.id,
                        "title": q.title,
                        "category": q.category or "",
                        "difficulty": q.difficulty or "medium",
                        "content": q.content or q.description or "",
                        "template_code": q.reference_solution or "",
                        "answer": q.answer or q.reference_solution or "",
                        "language": "text",
                        "is_answered": False,
                        "user_answer": "",
                        "score": None,
                        "ai_feedback": None,
                        "parsed_feedback": None,
                        "record_id": None,
                        "_source": "interview_question",
                    }
                )
            if not source_type:
                source_type = "mixed"

    if not selected:
        fallback_eq = select(Exercise).where(Exercise.is_public).limit(50)
        fr = await db.execute(fallback_eq)
        fallback_exercises = fr.scalars().all()
        if fallback_exercises:
            for ex in random.sample(fallback_exercises, min(body.question_count, len(fallback_exercises))):
                selected.append(
                    {
                        "id": ex.id,
                        "title": ex.title,
                        "category": ex.category or "",
                        "difficulty": ex.difficulty or "medium",
                        "content": ex.description or ex.instructions or "",
                        "template_code": ex.code_template or "",
                        "answer": ex.solution or ex.expected_output or "",
                        "language": ex.exercise_type or "text",
                        "is_answered": False,
                        "user_answer": "",
                        "score": None,
                        "ai_feedback": None,
                        "parsed_feedback": None,
                        "record_id": None,
                        "_source": "exercise",
                    }
                )
            source_type = "exercise_fallback"

    if not selected:
        raise NotFoundException("没有找到可用的面试/练习题目，请先在习题库或面试题库中添加题目")

    try:
        from sqlalchemy import text as sa_text

        # 只放弃同一批面试的旧会话（通过 position/level/type 匹配），而非所有会话
        await db.execute(
            sa_text(
                "UPDATE interview_sessions SET status='abandoned' "
                "WHERE user_id=:uid AND status IN ('started', 'submitted') "
                "AND (position=:pos OR title LIKE :title_pattern)"
            ).bindparams(
                uid=current_user.id,
                pos=body.position,
                title_pattern=f"%{body.position.replace('%', '\\%').replace('_', '\\_')}%",
            )
        )
        await db.commit()
    except Exception as e:
        logger.warning(f"清理旧面试会话时出错: {e}")
        await db.rollback()

    first_item = selected[0]
    session = InterviewSession(
        user_id=current_user.id,
        title=f"{body.position}-{body.type}模拟面试",
        question_id=first_item["id"],
        status="started",
        position=body.position,
        level=body.level,
        interview_type=body.type,
        start_time=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    for item in selected:
        item.pop("_source", None)

    return SuccessResponse(
        data={
            "session_id": session.id,
            "session": InterviewSessionDetail.model_validate(session).model_dump(),
            "questions": selected,
            "total_questions": len(selected),
            "source": source_type,
        },
        message="面试会话创建成功",
    )


@router.get(
    "/sessions",
    response_model=SuccessResponse[PaginationResponse[InterviewSessionWithQuestion]],
)
async def list_my_interview_sessions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="按状态筛选: started/submitted/finished/abandoned"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的面试会话列表
    只能查看自己的会话，支持分页和状态筛选
    """
    # 构建基础查询 - 只查询当前用户的会话（LEFT JOIN兼容旧会话）
    query = (
        select(
            InterviewSession,
            InterviewQuestion.title.label("question_title"),
            InterviewQuestion.difficulty.label("question_difficulty"),
        )
        .outerjoin(InterviewQuestion, InterviewSession.question_id == InterviewQuestion.id)
        .where(InterviewSession.user_id == current_user.id)
    )

    # 状态筛选
    if status_filter and status_filter.lower() in [
        "started",
        "submitted",
        "finished",
        "abandoned",
    ]:
        query = query.where(InterviewSession.status == status_filter.lower())

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 计算分页
    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    # 执行查询
    query = query.order_by(InterviewSession.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    rows = result.all()

    # 构建响应数据
    sessions_with_question = []
    for session, question_title, question_difficulty in rows:
        session_dict = {
            "id": session.id,
            "user_id": session.user_id,
            "question_id": session.question_id,
            "status": session.status,
            "started_at": session.started_at,
            "finished_at": session.finished_at,
            "latest_score": session.latest_score,
            "latest_submission_id": session.latest_submission_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "question_title": question_title,
            "question_difficulty": question_difficulty,
            "title": getattr(session, "title", None),
            "position": getattr(session, "position", None),
            "level": getattr(session, "level", None),
            "interview_type": getattr(session, "interview_type", None),
        }
        sessions_with_question.append(InterviewSessionWithQuestion(**session_dict))

    # 创建分页响应
    pagination_response = PaginationResponse(
        items=sessions_with_question, total=total, page=page, size=size, pages=pages
    )

    return SuccessResponse(data=pagination_response, message=f"获取到 {len(sessions_with_question)} 个会话")


@router.get("/sessions/{session_id}", response_model=SuccessResponse[dict])
async def get_interview_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(InterviewSession).where(
        InterviewSession.id == session_id, InterviewSession.user_id == current_user.id
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise NotFoundException("会话不存在或您没有权限查看")

    sub_q = select(Submission).where(Submission.session_id == session_id).order_by(Submission.created_at)
    sub_res = await db.execute(sub_q)
    submissions = sub_res.scalars().all()

    answered_qids = {s.question_id: s for s in submissions}

    all_qids = list(answered_qids.keys())
    if session.question_id and session.question_id not in all_qids:
        all_qids.append(session.question_id)

    q_map = {}
    ex_map = {}
    if all_qids:
        q_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id.in_(all_qids)))
        q_map = {q.id: q for q in q_result.scalars().all()}
        ex_result = await db.execute(select(Exercise).where(Exercise.id.in_(all_qids)))
        ex_map = {ex.id: ex for ex in ex_result.scalars().all()}

    import json as _json

    question_list = []
    for qid in all_qids:
        q = q_map.get(qid)
        ex = ex_map.get(qid)
        sub = answered_qids.get(qid)
        parsed_fb = None
        if sub and sub.feedback_json:
            try:
                parsed_fb = _json.loads(sub.feedback_json)
            except (ValueError, TypeError):
                pass
        if ex:
            question_list.append(
                {
                    "id": qid,
                    "title": ex.title,
                    "category": ex.category or "",
                    "difficulty": ex.difficulty or "",
                    "content": ex.description or ex.instructions or "",
                    "template_code": ex.code_template or "",
                    "answer": ex.solution or ex.expected_output or None,
                    "language": ex.exercise_type or ("text" if not ex.code_template else "python"),
                    "is_answered": sub is not None,
                    "user_answer": sub.source_code if sub else "",
                    "score": sub.score if sub else None,
                    "ai_feedback": sub.feedback if sub else None,
                    "parsed_feedback": parsed_fb,
                    "record_id": sub.id if sub else None,
                }
            )
        elif q:
            question_list.append(
                {
                    "id": qid,
                    "title": q.title,
                    "category": q.category or "",
                    "difficulty": q.difficulty or "",
                    "content": (q.content or q.description or "") if q else "",
                    "template_code": (q.reference_solution or "") if q else "",
                    "answer": (q.answer or q.reference_solution or None) if q else None,
                    "language": "text",
                    "is_answered": sub is not None,
                    "user_answer": sub.source_code if sub else "",
                    "score": sub.score if sub else None,
                    "ai_feedback": sub.feedback if sub else None,
                    "parsed_feedback": parsed_fb,
                    "record_id": sub.id if sub else None,
                }
            )

    return SuccessResponse(
        data={
            "session_id": session.id,
            "session": InterviewSessionDetail.model_validate(session).model_dump(),
            "questions": question_list,
            "total_questions": len(question_list),
        },
        message="会话详情获取成功",
    )


@router.post("/sessions/{session_id}/complete", response_model=SuccessResponse[dict])
async def complete_interview_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await complete_session(session_id, current_user.id, db)
    if result is None:
        raise NotFoundException("会话不存在")
    return SuccessResponse(data=result, message="面试已结束")


@router.post(
    "/sessions/{session_id}/submissions",
    response_model=SuccessResponse[SubmissionDetail],
    status_code=status.HTTP_201_CREATED,
)
async def create_submission(
    session_id: int,
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _ai=Depends(require_ai_points("interview_text_eval")),
):
    """
    为面试会话提交代码
    用户对某个会话提交代码，保存提交记录
    """
    # 1. 验证session属于当前用户
    session_query = select(InterviewSession).where(
        InterviewSession.id == session_id, InterviewSession.user_id == current_user.id
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise NotFoundException("会话不存在或您没有权限访问")

    if session.status not in ("started", "submitted"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前会话状态为 {session.status}，无法提交代码",
        )

    # 2. 验证题目存在（通过session关联的question）
    qid = session.question_id
    question = None
    exercise = None
    question_source = "interview_question"

    iq_query = select(InterviewQuestion).where(InterviewQuestion.id == qid)
    if not current_user.is_admin:
        iq_query = iq_query.where(InterviewQuestion.is_published)
    iq_result = await db.execute(iq_query)
    question = iq_result.scalar_one_or_none()

    if not question:
        ex_query = select(Exercise).where(Exercise.id == qid)
        if not current_user.is_admin:
            ex_query = ex_query.where(Exercise.is_public)
        ex_result = await db.execute(ex_query)
        exercise = ex_result.scalar_one_or_none()
        if exercise:
            question_source = "exercise"

    if not question and not exercise:
        raise NotFoundException("题目不存在或您没有权限访问")

    # 3. 校验代码非空（由Pydantic的min_length=1保证）
    # 4. 验证session_id一致性
    if submission_data.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请求中的session_id与路径参数不匹配",
        )

    # 5. 创建提交记录
    new_submission = Submission(
        session_id=session_id,
        user_id=current_user.id,
        question_id=qid,
        question_source=question_source,
        language=submission_data.language,
        source_code=submission_data.source_code,
        execution_status="pending",
        ai_evaluation_status="pending",
    )

    db.add(new_submission)

    try:
        await db.flush()  # flush 后 new_submission.id 才有值
    except Exception as e:
        await db.rollback()
        logger.error(f"提交保存失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="提交保存失败，事务已回滚")

    # 6. 更新会话的最新提交ID（flush 后 id 已赋值）
    session.latest_submission_id = new_submission.id
    session.status = "submitted"

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"提交保存失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="提交保存失败，事务已回滚")
    await db.refresh(new_submission)

    # 6.5 确认积分扣费（面试文本评测，提交即扣费）
    # 注意：积分扣费和提交记录在同一个事务中，line 662 的 commit 已经一起提交了
    await _ai()

    # 7. 异步执行代码沙盒和AI评估（不阻塞响应）
    import asyncio
    import logging

    _logger = logging.getLogger(__name__)

    async def _execute_and_evaluate_safe():
        try:
            await interview_execution_service.execute_and_evaluate_submission_by_id(new_submission.id)
        except Exception as e:
            _logger.error(
                f"异步评估任务失败 submission_id={new_submission.id}: {e}",
                exc_info=True,
            )

    # 保存 task 引用，防止 GC 回收导致任务丢失
    _bg_task = asyncio.create_task(_execute_and_evaluate_safe())
    _bg_task.add_done_callback(lambda t: t.exception() if not t.cancelled() and t.exception() else None)

    return SuccessResponse(
        data=SubmissionDetail.model_validate(new_submission),
        message="代码提交成功，正在执行和评估",
    )


@router.get("/submissions/{submission_id}", response_model=SuccessResponse[SubmissionDetail])
async def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取提交记录详情
    只能查看自己的提交
    """
    query = select(Submission).where(
        Submission.id == submission_id,
        Submission.user_id == current_user.id,  # 确保只能查看自己的提交
    )

    result = await db.execute(query)
    submission = result.scalar_one_or_none()

    if not submission:
        raise NotFoundException("提交记录不存在或您没有权限查看")

    return SuccessResponse(data=SubmissionDetail.model_validate(submission), message="提交记录详情获取成功")


@router.get(
    "/submissions/{submission_id}/result",
    response_model=SuccessResponse[SubmissionResultDetail],
)
async def get_submission_result(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_submission_result_detail(submission_id, current_user.id, db)
    if result is None:
        raise NotFoundException("提交记录不存在或您没有权限查看")
    return SuccessResponse(
        data=SubmissionResultDetail.model_validate(result),
        message="提交结果详情获取成功",
    )


@router.get(
    "/history",
    response_model=SuccessResponse[PaginationResponse[SubmissionHistoryItem]],
)
async def get_my_interview_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    question_id: Optional[int] = Query(None, description="按题目ID筛选"),
    status: Optional[str] = Query(None, description="按状态筛选（执行状态或AI评估状态）"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_interview_history(
        current_user.id,
        db,
        page=page,
        size=size,
        question_id=question_id,
        status_filter=status,
        start_date=start_date,
        end_date=end_date,
    )
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    history_items = [SubmissionHistoryItem.model_validate(item) for item in result["items"]]
    pagination_response = PaginationResponse(
        items=history_items,
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"],
    )
    return SuccessResponse(data=pagination_response, message=f"获取到 {len(history_items)} 条历史记录")


@router.get("/statistics", response_model=SuccessResponse[UserInterviewStatistics])
async def get_my_interview_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_user_interview_statistics(current_user.id, db)
    return SuccessResponse(data=stats, message="统计信息获取成功")


@router.post("/follow-up")
async def generate_follow_up_question(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _ai=Depends(require_ai_points("interview_follow_up")),
):
    question_title = body.get("question_title", "")
    user_answer = body.get("user_answer", "")
    ai_feedback = body.get("ai_feedback", "")
    score = body.get("score", 0)

    if not user_answer:
        raise HTTPException(status_code=400, detail="user_answer 不能为空")

    try:
        result = await generate_follow_up(question_title, user_answer, ai_feedback, score, db)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=502, detail="AI 服务调用失败，积分已退还")
    await _ai()
    return result


@router.post("/report")
async def interview_report_route(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")
    result = await generate_interview_report(session_id, current_user.id, db)
    if result is None:
        raise NotFoundException("面试会话不存在")
    return result


@router.post("/questions/generate-answers", response_model=SuccessResponse[dict])
async def generate_reference_answers_route(
    body: Optional[dict] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    limit = (body or {}).get("limit", 20)
    result = await generate_reference_answers(db, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return SuccessResponse(
        data=result,
        message=f"完成：成功生成 {result['generated']} 个，跳过 {result['skipped']} 个，剩余约 {result.get('remaining', 0)} 个",
    )
