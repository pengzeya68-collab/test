from typing import Optional
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import NotFoundException
from fastapi_backend.deps.auth import get_current_active_user, require_admin
from fastapi_backend.models.models import InterviewQuestion, InterviewSession, Submission, User
from fastapi_backend.schemas.common import MessageResponse, SuccessResponse, PaginationResponse
from fastapi_backend.schemas.interview import CodeSubmission, AIEvaluationResponse, UserInterviewStatistics
from fastapi_backend.schemas.interview_question import (
    InterviewQuestionDetail,
    InterviewQuestionList,
    InterviewQuestionListResponse
)
from fastapi_backend.schemas.interview_session import (
    InterviewSessionCreate,
    InterviewSessionDetail,
    InterviewSessionList,
    InterviewSessionWithQuestion
)
from fastapi_backend.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionUpdate,
    SubmissionResultDetail,
    SubmissionHistoryItem
)
from fastapi_backend.services.ai_tutor_service import AITutorService
from fastapi_backend.services.interview_execution_service import interview_execution_service

router = APIRouter(prefix="/api/v1/interview", tags=["AI 模拟面试"])


async def _get_active_ai_config(db: AsyncSession):
    from fastapi_backend.models.models import AIConfig
    result = await db.execute(select(AIConfig).where(AIConfig.is_active == True))
    return result.scalar_one_or_none()


def get_ai_tutor():
    return AITutorService()


@router.post("/evaluate", response_model=SuccessResponse[AIEvaluationResponse])
async def evaluate_interview_code(
    submission: CodeSubmission,
    tutor: AITutorService = Depends(get_ai_tutor)
):
    """
    接收用户编写的面试代码，并由 AI 导师给出评分与优化建议。
    """
    result = await tutor.evaluate_code(submission)
    return SuccessResponse(data=result, message="代码评估完成")


@router.get("/admin/manage", response_model=SuccessResponse[MessageResponse])
async def manage_interview_questions(current_user: User = Depends(require_admin)):
    """
    管理员管理面试题目的示例接口。
    仅管理员可访问，用于演示权限保护。
    """
    message = MessageResponse(message=f"管理员 {current_user.username} 已进入面试题管理界面")
    return SuccessResponse(data=message, message="操作成功")


@router.get("/questions", response_model=SuccessResponse[InterviewQuestionListResponse])
async def list_interview_questions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（标题、描述、标签）"),
    difficulty: Optional[str] = Query(None, description="难度筛选: easy/medium/hard"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取面试题目列表，支持分页、搜索、筛选
    普通用户只能看到已发布的题目，管理员可以看到所有题目
    """
    # 构建基础查询
    query = select(InterviewQuestion)

    # 根据用户角色过滤发布状态
    if not current_user.is_admin:
        query = query.where(InterviewQuestion.is_published == True)

    # 关键词搜索
    if keyword:
        keyword_filter = or_(
            InterviewQuestion.title.contains(keyword),
            InterviewQuestion.description.contains(keyword),
            InterviewQuestion.tags.contains(keyword)
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
    list_response = InterviewQuestionListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

    return SuccessResponse(
        data=list_response,
        message=f"获取到 {len(items)} 道题目"
    )


@router.get("/questions/{question_id}", response_model=SuccessResponse[InterviewQuestionDetail])
async def get_interview_question(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取面试题目详情
    普通用户只能查看已发布的题目，管理员可以查看所有题目
    """
    query = select(InterviewQuestion).where(InterviewQuestion.id == question_id)

    # 普通用户只能查看已发布的题目
    if not current_user.is_admin:
        query = query.where(InterviewQuestion.is_published == True)

    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在或您没有权限查看")

    return SuccessResponse(
        data=InterviewQuestionDetail.model_validate(question),
        message="题目详情获取成功"
    )


@router.post("/sessions", response_model=SuccessResponse[InterviewSessionDetail], status_code=status.HTTP_201_CREATED)
async def create_interview_session(
    session_data: InterviewSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新的面试会话
    用户点击"开始面试"时调用，为指定题目创建新的会话
    """
    # 验证题目是否存在且已发布（对普通用户）
    question_query = select(InterviewQuestion).where(InterviewQuestion.id == session_data.question_id)
    if not current_user.is_admin:
        question_query = question_query.where(InterviewQuestion.is_published == True)

    question_result = await db.execute(question_query)
    question = question_result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在或您没有权限访问")

    # 检查是否已有进行中的会话
    active_session_query = select(InterviewSession).where(
        InterviewSession.user_id == current_user.id,
        InterviewSession.question_id == session_data.question_id,
        InterviewSession.status.in_(["started", "submitted"])
    )
    active_result = await db.execute(active_session_query)
    active_session = active_result.scalar_one_or_none()

    if active_session:
        # 返回已存在的进行中会话
        return SuccessResponse(
            data=InterviewSessionDetail.model_validate(active_session),
            message="已存在进行中的会话，继续使用该会话"
        )

    # 创建新会话
    new_session = InterviewSession(
        user_id=current_user.id,
        question_id=session_data.question_id,
        status="started"
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return SuccessResponse(
        data=InterviewSessionDetail.model_validate(new_session),
        message="面试会话创建成功"
    )


class BatchSessionCreate(BaseModel):
    """批量创建面试会话"""
    position: str = Field(default="测试工程师", description="目标岗位")
    level: str = Field(default="中级", description="难度级别")
    type: str = Field(default="技术面", description="面试类型")
    question_count: int = Field(default=10, ge=1, le=50, description="题目数量")
    categories: list[str] = Field(default_factory=list, description="考察范围分类")


@router.post("/sessions/batch", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_batch_interview_session(
    body: BatchSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    import random

    difficulty_map = {"初级": "easy", "中级": "medium", "高级": "hard"}
    difficulty = difficulty_map.get(body.level, None)

    query = select(InterviewQuestion).where(InterviewQuestion.is_published == True)
    if body.categories:
        valid_cats = [c for c in body.categories if c != "其他"]
        if valid_cats:
            query = query.where(InterviewQuestion.category.in_(valid_cats))
    if difficulty:
        query = query.where(InterviewQuestion.difficulty == difficulty)

    result = await db.execute(query)
    all_questions = result.scalars().all()

    if not all_questions:
        fallback = select(InterviewQuestion).where(InterviewQuestion.is_published == True)
        result = await db.execute(fallback)
        all_questions = result.scalars().all()

    if not all_questions:
        raise NotFoundException("没有找到可用的面试题目，请先添加题目")

    selected = random.sample(all_questions, min(body.question_count, len(all_questions)))

    try:
        from sqlalchemy import text as sa_text
        await db.execute(
            sa_text(
                "UPDATE interview_sessions SET status='abandoned' WHERE user_id=:uid AND status IN ('started', 'submitted')"
            ).bindparams(uid=current_user.id)
        )
        await db.commit()
    except Exception as e:
        logger.warning(f"清理旧面试会话时出错: {e}")
        await db.rollback()

    first_question = selected[0]
    session = InterviewSession(
        user_id=current_user.id,
        title=f"{body.position}-{body.type}模拟面试",
        question_id=first_question.id,
        status="started",
        position=body.position,
        level=body.level,
        interview_type=body.type,
        start_time=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    question_list = []
    for q in selected:
        question_list.append({
            "id": q.id,
            "title": q.title,
            "category": q.category,
            "difficulty": q.difficulty,
            "content": q.content or q.description or "",
            "template_code": q.reference_solution or "",
            "answer": q.answer or q.reference_solution or "",
            "is_answered": False,
            "user_answer": "",
            "score": None,
            "ai_feedback": None,
            "record_id": None,
        })

    return SuccessResponse(
        data={
            "session_id": session.id,
            "session": InterviewSessionDetail.model_validate(session).model_dump(),
            "questions": question_list,
            "total_questions": len(question_list),
        },
        message="面试会话创建成功",
    )


@router.get("/sessions", response_model=SuccessResponse[PaginationResponse[InterviewSessionWithQuestion]])
async def list_my_interview_sessions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="按状态筛选: started/submitted/finished/abandoned"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
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
            InterviewQuestion.difficulty.label("question_difficulty")
        )
        .outerjoin(InterviewQuestion, InterviewSession.question_id == InterviewQuestion.id)
        .where(InterviewSession.user_id == current_user.id)
    )

    # 状态筛选
    if status_filter and status_filter.lower() in ["started", "submitted", "finished", "abandoned"]:
        query = query.where(InterviewSession.status == status_filter.lower())

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 计算分页
    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    # 执行查询
    query = (
        query.order_by(InterviewSession.created_at.desc())
        .offset(offset)
        .limit(size)
    )
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
            "question_difficulty": question_difficulty
        }
        sessions_with_question.append(InterviewSessionWithQuestion(**session_dict))

    # 创建分页响应
    pagination_response = PaginationResponse(
        items=sessions_with_question,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

    return SuccessResponse(
        data=pagination_response,
        message=f"获取到 {len(sessions_with_question)} 个会话"
    )


@router.get("/sessions/{session_id}", response_model=SuccessResponse[dict])
async def get_interview_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(InterviewSession).where(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
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
    if all_qids:
        q_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id.in_(all_qids)))
        q_map = {q.id: q for q in q_result.scalars().all()}

    question_list = []
    for qid in all_qids:
        q = q_map.get(qid)
        sub = answered_qids.get(qid)
        question_list.append({
            "id": qid,
            "title": q.title if q else "",
            "category": q.category if q else "",
            "difficulty": q.difficulty if q else "",
            "content": (q.content or q.description or "") if q else "",
            "template_code": (q.reference_solution or "") if q else "",
            "answer": (q.answer or q.reference_solution or None) if q else None,
            "is_answered": sub is not None,
            "user_answer": sub.source_code if sub else "",
            "score": sub.score if sub else None,
            "ai_feedback": sub.feedback if sub else None,
            "record_id": sub.id if sub else None,
        })

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
    query = select(InterviewSession).where(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundException("会话不存在")

    session.status = "finished"
    session.finished_at = datetime.utcnow()
    session.end_time = datetime.utcnow()

    sub_q = select(Submission).where(Submission.session_id == session_id)
    sub_res = await db.execute(sub_q)
    submissions = sub_res.scalars().all()
    scores = [s.score for s in submissions if s.score is not None]
    if scores:
        avg = sum(scores) / len(scores)
        session.latest_score = int(avg)
        session.user_score = int(avg)
        session.total_score = 100

    await db.commit()
    await db.refresh(session)

    return SuccessResponse(
        data={
            "session_id": session.id,
            "status": session.status,
            "score": session.latest_score,
            "total_questions": len(submissions),
            "answered_questions": len(submissions),
        },
        message="面试已结束",
    )


@router.post("/sessions/{session_id}/submissions", response_model=SuccessResponse[SubmissionDetail], status_code=status.HTTP_201_CREATED)
async def create_submission(
    session_id: int,
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为面试会话提交代码
    用户对某个会话提交代码，保存提交记录
    """
    # 1. 验证session属于当前用户
    session_query = select(InterviewSession).where(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise NotFoundException("会话不存在或您没有权限访问")

    # 2. 验证题目存在（通过session关联的question）
    question_query = select(InterviewQuestion).where(InterviewQuestion.id == session.question_id)
    if not current_user.is_admin:
        question_query = question_query.where(InterviewQuestion.is_published == True)

    question_result = await db.execute(question_query)
    question = question_result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在或您没有权限访问")

    # 3. 校验代码非空（由Pydantic的min_length=1保证）
    # 4. 验证session_id一致性
    if submission_data.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请求中的session_id与路径参数不匹配"
        )

    # 5. 创建提交记录
    new_submission = Submission(
        session_id=session_id,
        user_id=current_user.id,
        question_id=session.question_id,
        language=submission_data.language,
        source_code=submission_data.source_code,
        execution_status="pending",
        ai_evaluation_status="pending"
    )

    db.add(new_submission)

    # 6. 更新会话的最新提交ID（与提交记录在同一事务中）
    session.latest_submission_id = new_submission.id
    session.status = "submitted"

    try:
        await db.flush()
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="提交保存失败，事务已回滚")
    await db.refresh(new_submission)

    # 7. 异步执行代码沙盒和AI评估（不阻塞响应）
    import asyncio
    import logging
    _logger = logging.getLogger(__name__)

    async def _execute_and_evaluate_safe():
        try:
            await interview_execution_service.execute_and_evaluate_submission_by_id(new_submission.id)
        except Exception as e:
            _logger.error(f"异步评估任务失败 submission_id={new_submission.id}: {e}", exc_info=True)

    asyncio.create_task(_execute_and_evaluate_safe())

    return SuccessResponse(
        data=SubmissionDetail.model_validate(new_submission),
        message="代码提交成功，正在执行和评估"
    )


@router.get("/submissions/{submission_id}", response_model=SuccessResponse[SubmissionDetail])
async def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取提交记录详情
    只能查看自己的提交
    """
    query = select(Submission).where(
        Submission.id == submission_id,
        Submission.user_id == current_user.id  # 确保只能查看自己的提交
    )

    result = await db.execute(query)
    submission = result.scalar_one_or_none()

    if not submission:
        raise NotFoundException("提交记录不存在或您没有权限查看")

    return SuccessResponse(
        data=SubmissionDetail.model_validate(submission),
        message="提交记录详情获取成功"
    )


@router.get("/submissions/{submission_id}/result", response_model=SuccessResponse[SubmissionResultDetail])
async def get_submission_result(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取提交结果详情 - 完整评估报告
    包括题目信息、源码、执行结果、测试用例结果、AI评分等
    只能查看自己的提交
    """
    # 构建查询：获取提交记录及其关联的会话和题目信息
    query = (
        select(
            Submission,
            InterviewSession.status.label("session_status"),
            InterviewQuestion.title.label("question_title"),
            InterviewQuestion.difficulty.label("question_difficulty"),
            InterviewQuestion.description.label("question_description"),
            InterviewQuestion.prompt.label("question_prompt"),
            InterviewQuestion.test_cases.label("question_test_cases")
        )
        .join(InterviewSession, Submission.session_id == InterviewSession.id)
        .join(InterviewQuestion, Submission.question_id == InterviewQuestion.id)
        .where(
            Submission.id == submission_id,
            Submission.user_id == current_user.id  # 只能查看自己的提交
        )
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise NotFoundException("提交记录不存在或您没有权限查看")

    # 解包结果
    submission, session_status, question_title, question_difficulty, \
        question_description, question_prompt, question_test_cases = row

    # 构建结果字典
    result_dict = {
        "id": submission.id,
        "session_id": submission.session_id,
        "user_id": submission.user_id,
        "question_id": submission.question_id,
        "language": submission.language,
        "source_code": submission.source_code,
        "execution_status": submission.execution_status,
        "ai_evaluation_status": submission.ai_evaluation_status,
        "score": submission.score,
        "feedback": submission.feedback,
        "execution_result": submission.execution_result,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at,
        "session_status": session_status,
        "question_title": question_title,
        "question_difficulty": question_difficulty,
        "question_description": question_description,
        "question_prompt": question_prompt,
        "question_test_cases": question_test_cases
    }

    return SuccessResponse(
        data=SubmissionResultDetail.model_validate(result_dict),
        message="提交结果详情获取成功"
    )


@router.get("/history", response_model=SuccessResponse[PaginationResponse[SubmissionHistoryItem]])
async def get_my_interview_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    question_id: Optional[int] = Query(None, description="按题目ID筛选"),
    status: Optional[str] = Query(None, description="按状态筛选（执行状态或AI评估状态）"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取我的面试历史记录
    支持分页、题目筛选、状态筛选、时间筛选
    仅返回当前用户自己的数据
    """
    from sqlalchemy import or_

    # 构建基础查询（LEFT JOIN兼容旧数据）
    query = (
        select(
            Submission,
            InterviewQuestion.title.label("question_title"),
            InterviewQuestion.difficulty.label("question_difficulty")
        )
        .outerjoin(InterviewQuestion, Submission.question_id == InterviewQuestion.id)
        .where(Submission.user_id == current_user.id)  # 只返回当前用户的数据
        .order_by(Submission.created_at.desc())
    )

    # 题目筛选
    if question_id is not None:
        query = query.where(Submission.question_id == question_id)

    # 状态筛选（匹配执行状态或AI评估状态）
    if status is not None:
        query = query.where(
            or_(
                Submission.execution_status == status,
                Submission.ai_evaluation_status == status
            )
        )

    # 时间筛选
    if start_date is not None:
        from datetime import datetime
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(Submission.created_at >= start_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式无效，请使用 YYYY-MM-DD 格式"
            )

    if end_date is not None:
        from datetime import datetime, timedelta
        try:
            # 结束日期包括当天
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.where(Submission.created_at < end_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式无效，请使用 YYYY-MM-DD 格式"
            )

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 计算分页
    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    # 执行查询
    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    rows = result.all()

    # 构建历史项列表
    history_items = []
    for submission, question_title, question_difficulty in rows:
        item_dict = {
            "id": submission.id,
            "session_id": submission.session_id,
            "question_id": submission.question_id,
            "question_title": question_title,
            "question_difficulty": question_difficulty,
            "language": submission.language,
            "execution_status": submission.execution_status,
            "ai_evaluation_status": submission.ai_evaluation_status,
            "score": submission.score,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at
        }
        history_items.append(SubmissionHistoryItem.model_validate(item_dict))

    # 构建分页响应
    pagination_response = PaginationResponse(
        items=history_items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

    return SuccessResponse(
        data=pagination_response,
        message=f"获取到 {len(history_items)} 条历史记录"
    )


@router.get("/statistics", response_model=SuccessResponse[UserInterviewStatistics])
async def get_my_interview_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的面试统计信息
    用于个人成长面板展示
    """
    from datetime import datetime, timedelta, date
    from sqlalchemy import func, case, cast, Float

    # 获取当前时间
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    seven_days_ago = now - timedelta(days=7)

    # 1. 基础统计：总提交数
    total_query = select(func.count(Submission.id)).where(
        Submission.user_id == current_user.id
    )
    total_result = await db.execute(total_query)
    total_submissions = total_result.scalar_one() or 0

    # 2. 已完成评估的提交数（有分数）
    completed_query = select(func.count(Submission.id)).where(
        Submission.user_id == current_user.id,
        Submission.score.is_not(None)
    )
    completed_result = await db.execute(completed_query)
    completed_submissions = completed_result.scalar_one() or 0

    # 3. 分数统计：平均分、最高分、最低分
    score_stats_query = select(
        func.avg(Submission.score).label("avg_score"),
        func.max(Submission.score).label("max_score"),
        func.min(Submission.score).label("min_score")
    ).where(
        Submission.user_id == current_user.id,
        Submission.score.is_not(None)
    )
    score_stats_result = await db.execute(score_stats_query)
    score_stats = score_stats_result.first()

    average_score = float(score_stats.avg_score) if score_stats.avg_score else None
    highest_score = score_stats.max_score
    lowest_score = score_stats.min_score

    # 4. 通过率统计（分数≥80为通过）
    pass_stats_query = select(
        func.count(Submission.id).label("total"),
        func.sum(case((Submission.score >= 80, 1), else_=0)).label("passed")
    ).where(
        Submission.user_id == current_user.id,
        Submission.score.is_not(None)
    )
    pass_stats_result = await db.execute(pass_stats_query)
    pass_stats = pass_stats_result.first()

    total_with_score = pass_stats.total or 0
    passed_count = pass_stats.passed or 0 if pass_stats.passed else 0
    failed_count = total_with_score - passed_count
    pass_rate = (passed_count / total_with_score * 100) if total_with_score > 0 else 0.0

    # 5. 时间统计：最近7天提交量、今日提交量
    recent_7_days_query = select(func.count(Submission.id)).where(
        Submission.user_id == current_user.id,
        Submission.created_at >= seven_days_ago
    )
    recent_7_days_result = await db.execute(recent_7_days_query)
    recent_7_days_submissions = recent_7_days_result.scalar_one() or 0

    today_query = select(func.count(Submission.id)).where(
        Submission.user_id == current_user.id,
        Submission.created_at >= today_start
    )
    today_result = await db.execute(today_query)
    today_submissions = today_result.scalar_one() or 0

    # 6. 难度分布（连接题目表）
    difficulty_query = (
        select(
            InterviewQuestion.difficulty,
            func.count(Submission.id).label("count")
        )
        .join(InterviewQuestion, Submission.question_id == InterviewQuestion.id)
        .where(Submission.user_id == current_user.id)
        .group_by(InterviewQuestion.difficulty)
    )
    difficulty_result = await db.execute(difficulty_query)
    difficulty_rows = difficulty_result.all()

    difficulty_distribution = {}
    for difficulty, count in difficulty_rows:
        if difficulty:
            difficulty_distribution[difficulty] = count

    # 7. 最近7天每日提交量（用于图表）
    daily_submissions = []
    for i in range(6, -1, -1):  # 从6天前到今天
        day_start = datetime(now.year, now.month, now.day) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        day_query = select(func.count(Submission.id)).where(
            Submission.user_id == current_user.id,
            Submission.created_at >= day_start,
            Submission.created_at < day_end
        )
        day_result = await db.execute(day_query)
        day_count = day_result.scalar_one() or 0

        daily_submissions.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": day_count
        })

    # 8. 弱项标签统计（按题目标签和平均分）
    # 先获取所有有分数的提交及其题目标签
    # 由于标签是JSON字符串，这里简化处理：只统计有标签的数据
    # 实际项目中可能需要更复杂的JSON解析
    weak_tags = []  # 简化实现，实际需要解析题目标签

    # 9. 最近一次提交时间
    last_submission_query = select(Submission.created_at).where(
        Submission.user_id == current_user.id
    ).order_by(Submission.created_at.desc()).limit(1)
    last_submission_result = await db.execute(last_submission_query)
    last_submission_row = last_submission_result.scalar_one_or_none()
    last_submission_time = last_submission_row

    # 构建统计响应
    statistics = UserInterviewStatistics(
        total_submissions=total_submissions,
        completed_submissions=completed_submissions,
        average_score=average_score,
        highest_score=highest_score,
        lowest_score=lowest_score,
        pass_rate=pass_rate,
        passed_count=passed_count,
        failed_count=failed_count,
        recent_7_days_submissions=recent_7_days_submissions,
        today_submissions=today_submissions,
        difficulty_distribution=difficulty_distribution,
        daily_submissions_last_7_days=daily_submissions,
        weak_tags=weak_tags,
        last_submission_time=last_submission_time
    )

    return SuccessResponse(
        data=statistics,
        message="统计信息获取成功"
    )


@router.post("/follow-up")
async def generate_follow_up_question(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    question_title = body.get("question_title", "")
    user_answer = body.get("user_answer", "")
    ai_feedback = body.get("ai_feedback", "")
    score = body.get("score", 0)

    if not user_answer:
        raise HTTPException(status_code=400, detail="user_answer 不能为空")

    ai_config = await _get_active_ai_config(db)

    if ai_config:
        try:
            prompt = f"""你是一位资深测试开发面试官。候选人刚刚回答了以下面试题：

题目：{question_title}
候选人回答：{user_answer}
AI评分：{score}/100
AI点评：{ai_feedback}

请基于候选人的回答，生成一个追问问题。要求：
1. 追问应该针对候选人回答中的薄弱点或模糊之处
2. 追问应该考察更深层次的理解，而非表面记忆
3. 追问应该与测试开发实际工作场景相关
4. 追问要简洁明了，一个问题即可

请以JSON格式返回：{{"follow_up_question": "追问内容", "follow_up_type": "depth|practical|edge_case", "hint": "回答提示"}}"""

            import json as _json
            import httpx
            http_client = httpx.AsyncClient(timeout=ai_config.timeout_seconds, trust_env=False)
            try:
                from openai import AsyncOpenAI
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
                        {"role": "system", "content": "你是一位资深测试开发面试官，擅长追问来考察候选人的深度理解。请以JSON格式回复。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=300,
                    extra_body=extra_body,
                )
                await client.close()

                content = response.choices[0].message.content if response.choices else ""
                try:
                    result = _json.loads(content)
                    return {
                        "follow_up_question": result.get("follow_up_question", content),
                        "follow_up_type": result.get("follow_up_type", "depth"),
                        "hint": result.get("hint", ""),
                    }
                except _json.JSONDecodeError:
                    return {
                        "follow_up_question": content,
                        "follow_up_type": "depth",
                        "hint": "",
                    }
            finally:
                try:
                    await http_client.aclose()
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"AI追问生成失败: {e}")

    import random
    follow_ups = [
        f"你刚才回答了关于「{question_title}」的问题，能详细说说你在实际项目中是如何应用这个知识的吗？",
        f"你的回答提到了一些关键点，能再深入解释一下其中的原理吗？",
        f"如果在这个场景下遇到了边界情况，你会怎么处理？",
    ]
    return {
        "follow_up_question": random.choice(follow_ups),
        "follow_up_type": "depth",
        "hint": "追问是为了考察你的深度理解，请结合实际经验回答",
    }


@router.post("/report")
async def generate_interview_report(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    生成面试报告：综合评价 + 能力维度分析 + 改进路线
    """
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")

    session_query = select(InterviewSession).where(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id,
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    if not session:
        raise NotFoundException("面试会话不存在")

    submissions_query = (
        select(Submission)
        .where(Submission.session_id == session_id)
        .order_by(Submission.created_at)
    )
    submissions_result = await db.execute(submissions_query)
    submissions = submissions_result.scalars().all()

    total_questions = len(submissions)
    if total_questions == 0:
        return {
            "overall_score": 0,
            "overall_level": "未评估",
            "summary": "本次面试未提交任何回答",
            "dimensions": [],
            "strengths": [],
            "weaknesses": [],
            "improvement_plan": [],
        }

    scores = [s.score for s in submissions if s.score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    pass_count = sum(1 for s in scores if s >= 60)

    level = "专家" if avg_score >= 90 else "精通" if avg_score >= 80 else "熟练" if avg_score >= 70 else "掌握" if avg_score >= 60 else "了解" if avg_score >= 40 else "入门"

    high_score_submissions = [s for s in submissions if s.score and s.score >= 80]
    low_score_submissions = [s for s in submissions if s.score and s.score < 60]

    strengths = []
    for s in high_score_submissions[:3]:
        q_query = select(InterviewQuestion).where(InterviewQuestion.id == s.question_id)
        q_result = await db.execute(q_query)
        q = q_result.scalar_one_or_none()
        if q:
            strengths.append(f"{q.title}（{s.score}分）")

    weaknesses = []
    for s in low_score_submissions[:3]:
        q_query = select(InterviewQuestion).where(InterviewQuestion.id == s.question_id)
        q_result = await db.execute(q_query)
        q = q_result.scalar_one_or_none()
        if q:
            weaknesses.append(f"{q.title}（{s.score}分）")

    improvement_plan = []
    if avg_score < 60:
        improvement_plan = [
            "建议先巩固基础知识，重点复习测试理论和测试用例设计方法",
            "每天至少完成3道练习题，建立知识体系",
            "关注薄弱环节，针对性练习",
        ]
    elif avg_score < 80:
        improvement_plan = [
            "基础已较扎实，建议深入学习自动化测试和接口测试",
            "尝试参与实际项目，积累实战经验",
            "学习CI/CD和云原生相关技能，提升综合能力",
        ]
    else:
        improvement_plan = [
            "你已经具备较强的测试开发能力",
            "建议向测试架构师方向发展，学习测试平台开发",
            "可以尝试指导新人，提升技术影响力",
        ]

    return {
        "overall_score": round(avg_score, 1),
        "overall_level": level,
        "summary": f"本次面试共 {total_questions} 题，平均得分 {round(avg_score, 1)} 分，通过 {pass_count}/{total_questions} 题",
        "score_range": {"max": max_score, "min": min_score, "avg": round(avg_score, 1)},
        "pass_rate": round(pass_count / total_questions * 100, 1) if total_questions > 0 else 0,
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "improvement_plan": improvement_plan,
    }
