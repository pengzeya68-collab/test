from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import NotFoundException
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import InterviewQuestion, User, TestCase, Submission
from fastapi_backend.schemas.common import MessageResponse, SuccessResponse, PaginationResponse
from fastapi_backend.schemas.interview_question import (
    InterviewQuestionCreate,
    InterviewQuestionUpdate,
    InterviewQuestionDetail,
    InterviewQuestionList,
    InterviewQuestionListResponse
)
from fastapi_backend.schemas.test_case import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseDetail,
    TestCaseList,
    TestCaseListResponse,
    TestCaseBatchCreate,
    TestCaseBatchUpdate
)
from fastapi_backend.schemas.interview_statistics import (
    QuestionStatistics,
    QuestionStatisticsListResponse,
    OverallStatistics,
    SubmissionTrendResponse,
    DifficultyAnalysisResponse
)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/permission-check", response_model=MessageResponse)
async def admin_permission_check(current_user: User = Depends(require_admin)):
    return MessageResponse(message=f"Hello, admin {current_user.username}. Permission check passed.")


# 面试题目管理接口

@router.post("/interview/questions", response_model=SuccessResponse[InterviewQuestionDetail])
async def create_interview_question(
    question_data: InterviewQuestionCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建新的面试题目（仅管理员）"""
    existing = await db.execute(
        select(InterviewQuestion).where(InterviewQuestion.slug == question_data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"题目标识 '{question_data.slug}' 已存在"
        )

    new_question = InterviewQuestion(
        title=question_data.title,
        slug=question_data.slug,
        difficulty=question_data.difficulty,
        tags=question_data.tags,
        description=question_data.description,
        prompt=question_data.prompt,
        input_spec=question_data.input_spec,
        output_spec=question_data.output_spec,
        examples=question_data.examples,
        reference_solution=question_data.reference_solution,
        test_cases=question_data.test_cases,
        is_published=question_data.is_published
    )

    db.add(new_question)
    await db.commit()
    await db.refresh(new_question)

    return SuccessResponse(
        data=InterviewQuestionDetail.model_validate(new_question),
        message="题目创建成功"
    )


@router.get("/interview/questions", response_model=SuccessResponse[InterviewQuestionListResponse])
async def list_interview_questions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    is_published: Optional[bool] = Query(None, description="发布状态筛选"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取面试题目列表（仅管理员）"""
    query = select(InterviewQuestion)

    if keyword:
        keyword = keyword.strip()
        query = query.where(
            or_(
                InterviewQuestion.title.contains(keyword),
                InterviewQuestion.description.contains(keyword),
                InterviewQuestion.tags.contains(keyword)
            )
        )

    if difficulty and difficulty.lower() in ["easy", "medium", "hard"]:
        query = query.where(InterviewQuestion.difficulty == difficulty.lower())

    if is_published is not None:
        query = query.where(InterviewQuestion.is_published == is_published)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    query = query.order_by(InterviewQuestion.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    questions = result.scalars().all()

    items = [InterviewQuestionList.model_validate(q) for q in questions]

    list_response = InterviewQuestionListResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )

    return SuccessResponse(data=list_response, message=f"获取到 {len(items)} 条题目")


@router.get("/interview/questions/{question_id}", response_model=SuccessResponse[InterviewQuestionDetail])
async def get_interview_question(
    question_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取面试题目详情"""
    result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id))
    question = result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在")

    return SuccessResponse(data=InterviewQuestionDetail.model_validate(question), message="题目详情获取成功")


@router.put("/interview/questions/{question_id}", response_model=SuccessResponse[InterviewQuestionDetail])
async def update_interview_question(
    question_id: int,
    question_data: InterviewQuestionUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新面试题目"""
    result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id))
    question = result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在")

    if question_data.title is not None:
        question.title = question_data.title
    if question_data.slug is not None:
        if question_data.slug != question.slug:
            existing = await db.execute(
                select(InterviewQuestion).where(
                    InterviewQuestion.slug == question_data.slug,
                    InterviewQuestion.id != question_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=409, detail=f"题目标识 '{question_data.slug}' 已存在")
        question.slug = question_data.slug
    if question_data.difficulty is not None:
        question.difficulty = question_data.difficulty
    if question_data.tags is not None:
        question.tags = question_data.tags
    if question_data.description is not None:
        question.description = question_data.description
    if question_data.prompt is not None:
        question.prompt = question_data.prompt
    if question_data.input_spec is not None:
        question.input_spec = question_data.input_spec
    if question_data.output_spec is not None:
        question.output_spec = question_data.output_spec
    if question_data.examples is not None:
        question.examples = question_data.examples
    if question_data.reference_solution is not None:
        question.reference_solution = question_data.reference_solution
    if question_data.test_cases is not None:
        question.test_cases = question_data.test_cases
    if question_data.is_published is not None:
        question.is_published = question_data.is_published

    await db.commit()
    await db.refresh(question)

    return SuccessResponse(data=InterviewQuestionDetail.model_validate(question), message="题目更新成功")


@router.delete("/interview/questions/{question_id}", response_model=SuccessResponse[MessageResponse])
async def delete_interview_question(
    question_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除面试题目"""
    from fastapi_backend.models.models import InterviewSession

    result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id))
    question = result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在")

    session_count = await db.scalar(
        select(func.count()).select_from(InterviewSession).where(InterviewSession.question_id == question_id)
    ) or 0
    submission_count = await db.scalar(
        select(func.count()).select_from(Submission).where(Submission.question_id == question_id)
    ) or 0

    if session_count > 0 or submission_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"题目无法删除，已有 {session_count} 个会话和 {submission_count} 个提交记录"
        )

    await db.delete(question)
    await db.commit()

    return SuccessResponse(data=MessageResponse(message="题目删除成功"), message="题目删除成功")


@router.patch("/interview/questions/{question_id}/publish", response_model=SuccessResponse[InterviewQuestionDetail])
async def publish_interview_question(
    question_id: int,
    action: str = Query("publish", pattern="^(publish|unpublish)$"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """发布/下线面试题目"""
    result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id))
    question = result.scalar_one_or_none()

    if not question:
        raise NotFoundException("题目不存在")

    question.is_published = (action == "publish")
    message = "题目已发布" if action == "publish" else "题目已下线"

    await db.commit()
    await db.refresh(question)

    return SuccessResponse(data=InterviewQuestionDetail.model_validate(question), message=message)


# 面试题测试用例管理接口

@router.post("/interview/questions/{question_id}/test-cases", response_model=SuccessResponse[TestCaseDetail], status_code=status.HTTP_201_CREATED)
async def create_test_case(
    question_id: int,
    test_case_data: TestCaseCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """为面试题创建测试用例"""
    question = await db.get(InterviewQuestion, question_id)
    if not question:
        raise NotFoundException("题目不存在")

    if test_case_data.question_id != question_id:
        raise HTTPException(status_code=400, detail="question_id不匹配")

    new_test_case = TestCase(
        question_id=question_id,
        input=test_case_data.input,
        expected_output=test_case_data.expected_output,
        is_example=test_case_data.is_example,
        is_hidden=test_case_data.is_hidden,
        description=test_case_data.description
    )

    db.add(new_test_case)
    await db.commit()
    await db.refresh(new_test_case)

    return SuccessResponse(data=TestCaseDetail.model_validate(new_test_case), message="测试用例创建成功")


@router.get("/interview/questions/{question_id}/test-cases", response_model=SuccessResponse[TestCaseListResponse])
async def list_test_cases(
    question_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_example: Optional[bool] = Query(None),
    is_hidden: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取面试题测试用例列表"""
    question = await db.get(InterviewQuestion, question_id)
    if not question:
        raise NotFoundException("题目不存在")

    query = select(TestCase).where(TestCase.question_id == question_id)

    if is_example is not None:
        query = query.where(TestCase.is_example == is_example)
    if is_hidden is not None:
        query = query.where(TestCase.is_hidden == is_hidden)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    query = query.order_by(TestCase.created_at.asc()).offset(offset).limit(size)
    result = await db.execute(query)
    test_cases = result.scalars().all()

    items = [TestCaseList.model_validate(tc) for tc in test_cases]

    list_response = TestCaseListResponse(items=items, total=total, page=page, size=size, pages=pages)

    return SuccessResponse(data=list_response, message=f"获取到 {len(items)} 个测试用例")


@router.get("/interview/questions/{question_id}/test-cases/{test_case_id}", response_model=SuccessResponse[TestCaseDetail])
async def get_test_case(
    question_id: int,
    test_case_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例详情"""
    question = await db.get(InterviewQuestion, question_id)
    if not question:
        raise NotFoundException("题目不存在")

    test_case = await db.get(TestCase, test_case_id)
    if not test_case or test_case.question_id != question_id:
        raise NotFoundException("测试用例不存在")

    return SuccessResponse(data=TestCaseDetail.model_validate(test_case), message="获取成功")


@router.put("/interview/questions/{question_id}/test-cases/{test_case_id}", response_model=SuccessResponse[TestCaseDetail])
async def update_test_case(
    question_id: int,
    test_case_id: int,
    test_case_data: TestCaseUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例"""
    question = await db.get(InterviewQuestion, question_id)
    if not question:
        raise NotFoundException("题目不存在")

    test_case = await db.get(TestCase, test_case_id)
    if not test_case or test_case.question_id != question_id:
        raise NotFoundException("测试用例不存在")

    if test_case_data.input is not None:
        test_case.input = test_case_data.input
    if test_case_data.expected_output is not None:
        test_case.expected_output = test_case_data.expected_output
    if test_case_data.is_example is not None:
        test_case.is_example = test_case_data.is_example
    if test_case_data.is_hidden is not None:
        test_case.is_hidden = test_case_data.is_hidden
    if test_case_data.description is not None:
        test_case.description = test_case_data.description

    await db.commit()
    await db.refresh(test_case)

    return SuccessResponse(data=TestCaseDetail.model_validate(test_case), message="更新成功")


@router.delete("/interview/questions/{question_id}/test-cases/{test_case_id}", response_model=SuccessResponse[MessageResponse])
async def delete_test_case(
    question_id: int,
    test_case_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除测试用例"""
    question = await db.get(InterviewQuestion, question_id)
    if not question:
        raise NotFoundException("题目不存在")

    test_case = await db.get(TestCase, test_case_id)
    if not test_case or test_case.question_id != question_id:
        raise NotFoundException("测试用例不存在")

    await db.delete(test_case)
    await db.commit()

    return SuccessResponse(data=MessageResponse(message="测试用例删除成功"), message="删除成功")


@router.post("/interview/questions/{question_id}/test-cases/batch", response_model=SuccessResponse[list[TestCaseDetail]], status_code=status.HTTP_201_CREATED)
async def batch_create_test_cases(
    question_id: int,
    batch_data: TestCaseBatchCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """批量创建测试用例"""
    question = await db.get(InterviewQuestion, question_id)
    if not question:
        raise NotFoundException("题目不存在")

    created_cases = []
    for test_case_base in batch_data.test_cases:
        new_test_case = TestCase(
            question_id=question_id,
            input=test_case_base.input,
            expected_output=test_case_base.expected_output,
            is_example=test_case_base.is_example,
            is_hidden=test_case_base.is_hidden,
            description=test_case_base.description
        )
        db.add(new_test_case)
        created_cases.append(new_test_case)

    await db.commit()
    for tc in created_cases:
        await db.refresh(tc)

    return SuccessResponse(
        data=[TestCaseDetail.model_validate(tc) for tc in created_cases],
        message=f"批量创建 {len(created_cases)} 个测试用例成功"
    )


# 题库统计接口

@router.get("/interview/questions/statistics", response_model=SuccessResponse[QuestionStatisticsListResponse])
async def get_question_statistics(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    difficulty: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取题目维度统计信息"""
    from datetime import timedelta
    from sqlalchemy import case

    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    base_query = select(InterviewQuestion)

    if difficulty and difficulty.lower() in ["easy", "medium", "hard"]:
        base_query = base_query.where(InterviewQuestion.difficulty == difficulty.lower())
    if is_published is not None:
        base_query = base_query.where(InterviewQuestion.is_published == is_published)

    total = await db.scalar(select(func.count()).select_from(base_query.subquery()))
    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    base_query = base_query.order_by(InterviewQuestion.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(base_query)
    questions = result.scalars().all()

    statistics_items = []

    for question in questions:
        submission_filters = [Submission.question_id == question.id]

        if start_date:
            try:
                submission_filters.append(Submission.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
            except ValueError:
                raise HTTPException(status_code=400, detail="开始日期格式无效")
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                submission_filters.append(Submission.created_at < end_datetime)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束日期格式无效")

        total_submissions = await db.scalar(select(func.count(Submission.id)).where(*submission_filters)) or 0
        completed_submissions = await db.scalar(
            select(func.count(Submission.id)).where(*submission_filters, Submission.score.is_not(None))
        ) or 0

        score_stats = await db.execute(
            select(
                func.avg(Submission.score).label("avg_score"),
                func.max(Submission.score).label("max_score"),
                func.min(Submission.score).label("min_score")
            ).where(*submission_filters, Submission.score.is_not(None))
        )
        score_row = score_stats.first()
        average_score = float(score_row.avg_score) if score_row.avg_score else None

        pass_row = await db.execute(
            select(
                func.count(Submission.id).label("total"),
                func.sum(case((Submission.score >= 80, 1), else_=0)).label("passed")
            ).where(*submission_filters, Submission.score.is_not(None))
        )
        pass_data = pass_row.first()
        total_with_score = pass_data.total or 0
        passed_count = pass_data.passed or 0 if pass_data.passed else 0
        pass_rate = (passed_count / total_with_score * 100) if total_with_score > 0 else 0.0

        recent_7d = await db.scalar(
            select(func.count(Submission.id)).where(*submission_filters, Submission.created_at >= seven_days_ago)
        ) or 0
        recent_30d = await db.scalar(
            select(func.count(Submission.id)).where(*submission_filters, Submission.created_at >= thirty_days_ago)
        ) or 0

        last_submission = await db.scalar(
            select(Submission.created_at).where(*submission_filters).order_by(Submission.created_at.desc()).limit(1)
        )

        statistics_items.append(QuestionStatistics(
            question_id=question.id,
            title=question.title,
            slug=question.slug,
            difficulty=question.difficulty,
            is_published=question.is_published,
            total_submissions=total_submissions,
            completed_submissions=completed_submissions,
            average_score=average_score,
            highest_score=score_row.max_score,
            lowest_score=score_row.min_score,
            pass_rate=pass_rate,
            passed_count=passed_count,
            failed_count=total_with_score - passed_count,
            recent_7_days_submissions=recent_7d,
            recent_30_days_submissions=recent_30d,
            last_submission_time=last_submission,
            created_at=question.created_at
        ))

    list_response = QuestionStatisticsListResponse(
        items=statistics_items, total=total, page=page, size=size, pages=pages
    )

    return SuccessResponse(data=list_response, message=f"获取到 {len(statistics_items)} 个题目的统计信息")


@router.get("/interview/questions/overall-statistics", response_model=SuccessResponse[OverallStatistics])
async def get_overall_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取整体题库统计信息"""
    from datetime import timedelta
    from sqlalchemy import case

    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    submission_filters = []
    if start_date:
        try:
            submission_filters.append(Submission.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式无效")
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            submission_filters.append(Submission.created_at < end_datetime)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式无效")

    total_questions = await db.scalar(select(func.count(InterviewQuestion.id))) or 0
    published_questions = await db.scalar(
        select(func.count(InterviewQuestion.id)).where(InterviewQuestion.is_published == True)
    ) or 0

    total_submissions = await db.scalar(select(func.count(Submission.id)).where(*submission_filters)) or 0
    completed_submissions = await db.scalar(
        select(func.count(Submission.id)).where(*submission_filters, Submission.score.is_not(None))
    ) or 0

    score_stats = await db.execute(
        select(
            func.avg(Submission.score).label("avg_score"),
            func.max(Submission.score).label("max_score"),
            func.min(Submission.score).label("min_score")
        ).where(*submission_filters, Submission.score.is_not(None))
    )
    score_row = score_stats.first()
    average_score = float(score_row.avg_score) if score_row.avg_score else None

    pass_row = await db.execute(
        select(
            func.count(Submission.id).label("total"),
            func.sum(case((Submission.score >= 80, 1), else_=0)).label("passed")
        ).where(*submission_filters, Submission.score.is_not(None))
    )
    pass_data = pass_row.first()
    total_with_score = pass_data.total or 0
    passed_count = pass_data.passed or 0 if pass_data.passed else 0
    pass_rate = (passed_count / total_with_score * 100) if total_with_score > 0 else 0.0

    difficulty_dist = await db.execute(
        select(InterviewQuestion.difficulty, func.count(InterviewQuestion.id).label("count"))
        .group_by(InterviewQuestion.difficulty)
    )
    easy_count = medium_count = hard_count = 0
    for diff, cnt in difficulty_dist.all():
        if diff == "easy":
            easy_count = cnt
        elif diff == "medium":
            medium_count = cnt
        elif diff == "hard":
            hard_count = cnt

    recent_7d = await db.scalar(
        select(func.count(Submission.id)).where(*submission_filters, Submission.created_at >= seven_days_ago)
    ) or 0
    recent_30d = await db.scalar(
        select(func.count(Submission.id)).where(*submission_filters, Submission.created_at >= thirty_days_ago)
    ) or 0

    overall_stats = OverallStatistics(
        total_questions=total_questions,
        published_questions=published_questions,
        total_submissions=total_submissions,
        completed_submissions=completed_submissions,
        average_score=average_score,
        pass_rate=pass_rate,
        easy_count=easy_count,
        medium_count=medium_count,
        hard_count=hard_count,
        recent_7_days_activity=recent_7d,
        recent_30_days_activity=recent_30d,
        top_questions=[]
    )

    return SuccessResponse(data=overall_stats, message="整体统计信息获取成功")
