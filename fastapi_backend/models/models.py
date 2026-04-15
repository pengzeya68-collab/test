"""
数据模型 - 与实际数据库表名和列名匹配
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from fastapi_backend.core.database import Base


class User(Base):
    """Frontend user model mapped to the legacy Flask users table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_super_admin = Column(Boolean, default=False)
    level = Column(Integer, default=1)
    score = Column(Integer, default=0)
    study_time = Column(Integer, default=0)
    avatar = Column(String(500))

    @property
    def role(self) -> str:
        """用户角色：'admin' 或 'user'"""
        return "admin" if self.is_admin else "user"

    def __repr__(self):
        return f"<User {self.username}>"


class ApiGroup(Base):
    """接口分组表 - 支持树形层级结构"""
    __tablename__ = "auto_test_groups"

    id = Column(Integer, primary_key=True, index=True, comment="分组ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="分组名称")
    description = Column(String(500), nullable=True, comment="分组描述")
    parent_id = Column(Integer, ForeignKey("auto_test_groups.id"), nullable=True, comment="父分组ID，顶级分组为NULL")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 自关联关系
    children = relationship(
        "ApiGroup",
        backref="parent",
        remote_side=[id]
    )

    def __repr__(self):
        return f"<ApiGroup {self.name}>"


class ApiCase(Base):
    """接口用例表"""
    __tablename__ = "interface_test_cases"

    id = Column(Integer, primary_key=True, index=True, comment="用例ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    folder_id = Column(Integer, ForeignKey("interface_test_folders.id"), nullable=True, comment="所属目录ID")
    name = Column(String(200), nullable=False, comment="用例名称")
    description = Column(Text, nullable=True, comment="描述")
    url = Column(String(2000), nullable=False, comment="接口地址")
    method = Column(String(10), nullable=False, comment="请求方法: GET/POST/PUT/DELETE/PATCH")
    headers = Column(Text, nullable=True, comment="请求头 JSON 格式")
    body = Column(Text, nullable=True, comment="请求体 JSON/表单格式")
    body_type = Column(String(20), default="json", comment="请求体类型: json/form/text")
    is_public = Column(Boolean, default=False, comment="是否公开")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联目录
    folder = relationship("TestFolder", backref="cases")

    def __repr__(self):
        return f"<ApiCase {self.method} {self.name}>"


class TestFolder(Base):
    """接口测试文件夹表"""
    __tablename__ = "interface_test_folders"

    id = Column(Integer, primary_key=True, index=True, comment="目录ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="目录名称")
    parent_id = Column(Integer, nullable=True, comment="父目录ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class Environment(Base):
    """测试环境表"""
    __tablename__ = "interface_test_environments"

    id = Column(Integer, primary_key=True, index=True, comment="环境ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="环境名称")
    base_url = Column(String(500), nullable=True, comment="基础URL")
    variables = Column(Text, nullable=True, comment="环境变量 JSON 格式")
    is_default = Column(Boolean, default=False, comment="是否默认环境")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<Environment {self.name}>"


class TestPlan(Base):
    """测试计划表"""
    __tablename__ = "interface_test_plans"

    id = Column(Integer, primary_key=True, index=True, comment="计划ID")
    user_id = Column(Integer, nullable=False, comment="创建用户ID")
    name = Column(String(200), nullable=False, comment="计划名称")
    description = Column(Text, nullable=True, comment="计划描述")
    case_ids = Column(Text, nullable=False, comment="选中的用例ID JSON 数组")
    environment_id = Column(Integer, ForeignKey("interface_test_environments.id"), nullable=True, comment="测试环境ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<TestPlan {self.name}>"


class TestReport(Base):
    """测试报告表"""
    __tablename__ = "interface_test_reports"

    id = Column(Integer, primary_key=True, index=True, comment="报告ID")
    plan_id = Column(Integer, ForeignKey("interface_test_plans.id"), nullable=True, comment="所属计划ID")
    plan_name = Column(String(200), nullable=True, comment="计划名称快照")
    total_count = Column(Integer, default=0, comment="总用例数")
    success_count = Column(Integer, default=0, comment="成功数")
    failed_count = Column(Integer, default=0, comment="失败数")
    total_time = Column(Integer, default=0, comment="总耗时 毫秒")
    status = Column(String(20), default="pending", comment="状态: pending/running/completed/failed")
    executed_at = Column(DateTime, default=datetime.utcnow, comment="执行时间")

    # 关联
    results = relationship("TestReportResult", backref="report", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestReport {self.id} {self.plan_name}>"


class TestReportResult(Base):
    """测试结果表 - 单个用例执行结果"""
    __tablename__ = "interface_test_report_results"

    id = Column(Integer, primary_key=True, index=True, comment="结果ID")
    report_id = Column(Integer, ForeignKey("interface_test_reports.id"), nullable=False, comment="所属报告ID")
    case_id = Column(Integer, ForeignKey("interface_test_cases.id"), nullable=True, comment="执行用例ID")
    case_name = Column(String(200), nullable=True, comment="用例名称快照")
    method = Column(String(10), nullable=True, comment="请求方法")
    url = Column(String(2000), nullable=True, comment="请求URL")
    status_code = Column(Integer, nullable=True, comment="响应状态码")
    success = Column(Boolean, default=False, comment="是否成功")
    time = Column(Integer, default=0, comment="执行耗时 毫秒")
    error = Column(Text, nullable=True, comment="错误信息")
    request_headers = Column(Text, nullable=True, comment="请求头 JSON")
    request_body = Column(Text, nullable=True, comment="请求体")
    response = Column(Text, nullable=True, comment="响应体")
    response_headers = Column(Text, nullable=True, comment="响应头 JSON")
    executed_at = Column(DateTime, default=datetime.utcnow, comment="执行时间")

    def __repr__(self):
        return f"<TestReportResult {self.case_name} {self.status_code}>"


class InterviewQuestion(Base):
    """AI模拟面试题目表 - 兼容Flask旧字段和FastAPI新字段"""
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True, comment="题目ID")
    title = Column(String(500), nullable=False, comment="题目标题")
    # Flask 旧字段
    content = Column(Text, nullable=True, comment="题目内容（旧字段，兼容Flask）")
    answer = Column(Text, nullable=True, comment="参考答案（旧字段）")
    category = Column(String(50), nullable=True, comment="分类（旧字段）")
    position_level = Column(String(50), nullable=True, comment="职位级别（旧字段）")
    company = Column(String(100), nullable=True, comment="公司（旧字段）")
    view_count = Column(Integer, default=0, comment="浏览数（旧字段）")
    collect_count = Column(Integer, default=0, comment="收藏数（旧字段）")
    # FastAPI 新字段
    slug = Column(String(200), unique=True, nullable=True, comment="URL友好标识")
    difficulty = Column(String(20), default="medium", comment="难度: easy/medium/hard")
    tags = Column(Text, nullable=True, comment="标签列表 JSON/逗号分隔")
    description = Column(Text, nullable=True, comment="题目描述")
    prompt = Column(Text, nullable=True, comment="AI提示词")
    input_spec = Column(Text, nullable=True, comment="输入规范说明")
    output_spec = Column(Text, nullable=True, comment="输出规范说明")
    examples = Column(Text, nullable=True, comment="示例输入输出 JSON 格式")
    reference_solution = Column(Text, nullable=True, comment="参考答案")
    test_cases = Column(Text, nullable=True, default="", comment="测试用例 JSON 格式")
    is_published = Column(Boolean, default=True, comment="是否发布")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<InterviewQuestion {self.title} ({self.difficulty})>"


class InterviewSession(Base):
    """AI模拟面试会话表 - 兼容Flask旧字段和FastAPI新字段"""
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True, comment="会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    # Flask 旧字段
    title = Column(String(200), nullable=True, comment="会话标题（旧字段）")
    position = Column(String(100), nullable=True, comment="面试岗位（旧字段）")
    level = Column(String(50), nullable=True, comment="面试级别（旧字段）")
    interview_type = Column(String(50), nullable=True, comment="面试类型（旧字段）")
    total_score = Column(Integer, nullable=True, comment="总分（旧字段）")
    user_score = Column(Integer, nullable=True, comment="用户得分（旧字段）")
    start_time = Column(DateTime, nullable=True, comment="开始时间（旧字段）")
    end_time = Column(DateTime, nullable=True, comment="结束时间（旧字段）")
    feedback = Column(Text, nullable=True, comment="反馈（旧字段）")
    improvement_suggestions = Column(Text, nullable=True, comment="改进建议（旧字段）")
    # FastAPI 新字段
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=True, comment="题目ID")
    status = Column(String(20), default="started", comment="状态: started/submitted/finished/abandoned")
    started_at = Column(DateTime, default=datetime.utcnow, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")
    latest_score = Column(Integer, nullable=True, comment="最新成绩 (0-100)")
    latest_submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=True, comment="最新提交记录ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", backref="interview_sessions")
    question = relationship("InterviewQuestion", backref="sessions")
    latest_submission = relationship("Submission", foreign_keys=[latest_submission_id], post_update=True)

    def __repr__(self):
        return f"<InterviewSession {self.id} user:{self.user_id} question:{self.question_id} status:{self.status}>"


class Submission(Base):
    """代码提交记录表"""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True, comment="提交ID")
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, comment="会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False, comment="题目ID")
    language = Column(String(20), default="python", comment="编程语言")
    source_code = Column(Text, nullable=False, comment="源代码")
    execution_status = Column(String(20), default="pending", comment="执行状态: pending/running/success/failed")
    ai_evaluation_status = Column(String(20), default="pending", comment="AI评估状态: pending/running/completed/failed")
    score = Column(Integer, nullable=True, comment="AI评分 (0-100)")
    feedback = Column(Text, nullable=True, comment="AI反馈")
    execution_result = Column(Text, nullable=True, comment="执行结果 JSON 格式")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    session = relationship("InterviewSession", backref="submissions", foreign_keys=[session_id])
    user = relationship("User", backref="submissions", foreign_keys=[user_id])
    question = relationship("InterviewQuestion", backref="submissions", foreign_keys=[question_id])

    def __repr__(self):
        return f"<Submission {self.id} session:{self.session_id} user:{self.user_id} language:{self.language}>"


class LearningPath(Base):
    """学习路径表"""
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    learning_objectives = Column(Text)
    knowledge_outline = Column(Text)
    supporting_resources = Column(Text)
    prerequisites = Column(String(500))
    language = Column(String(50), nullable=False)
    difficulty = Column(String(20), default="beginner")
    stage = Column(Integer, default=1)
    estimated_hours = Column(Integer, default=10)
    exercise_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_id = Column(Integer, nullable=True)

    # Relationships
    exercises = relationship("Exercise", backref="learning_path", lazy="selectin")
    creator = relationship("User", foreign_keys=[user_id], backref="learning_paths")

    def __repr__(self):
        return f"<LearningPath {self.title}>"


class Exercise(Base):
    """习题表"""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    solution = Column(Text)
    difficulty = Column(String(20), default="easy")
    language = Column(String(50), nullable=False)
    module = Column(String(50), default="normal")
    category = Column(String(100))
    stage = Column(Integer, default=1)
    knowledge_point = Column(String(200))
    time_estimate = Column(Integer)
    is_public = Column(Boolean, default=True)
    exercise_type = Column(String(20), default="text")
    test_cases = Column(Text)
    code_template = Column(Text)
    expected_output = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_id = Column(Integer, nullable=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[user_id], backref="exercises")

    def __repr__(self):
        return f"<Exercise {self.title}>"


class Progress(Base):
    """学习进度表"""
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    completed = Column(Boolean, default=False)
    score = Column(Float)
    time_spent = Column(Integer)
    attempts = Column(Integer, default=0)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Post(Base):
    """社区帖子表"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(String(500))
    tags = Column(String(200))
    category = Column(String(50), nullable=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    is_essence = Column(Boolean, default=False)
    is_top = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", backref="posts")


class Comment(Base):
    """社区评论表"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"))

    user = relationship("User", backref="comments")
    post = relationship("Post", backref="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")


class Like(Base):
    """点赞表"""
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"))
    comment_id = Column(Integer, ForeignKey("comments.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # 注意：SQLite 不支持命名约束的 partial unique index，这里只做模型层面约束
    )


class Favorite(Base):
    """收藏表"""
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TestCase(Base):
    """面试题测试用例表"""
    __tablename__ = "interview_test_cases"

    id = Column(Integer, primary_key=True, index=True, comment="测试用例ID")
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False, comment="关联题目ID")
    input = Column(Text, nullable=False, comment="输入数据")
    expected_output = Column(Text, nullable=False, comment="预期输出")
    is_example = Column(Boolean, default=False, comment="是否为示例用例（用户可见）")
    is_hidden = Column(Boolean, default=False, comment="是否为隐藏用例（用户不可见，用于判题）")
    description = Column(Text, nullable=True, comment="用例描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    question = relationship("InterviewQuestion", backref="interview_test_cases")

    def __repr__(self):
        return f"<TestCase {self.id} question:{self.question_id} {'example' if self.is_example else 'hidden' if self.is_hidden else 'normal'}>"


# ---------------------------------------------------------------------------
# Exam system models
# ---------------------------------------------------------------------------


class Exam(Base):
    """考试表"""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    exam_type = Column(String(50), nullable=False, comment="模拟考试/正式考试/专项练习")
    difficulty = Column(String(20), default="medium", comment="easy/medium/hard")
    duration = Column(Integer, nullable=False, comment="考试时长（分钟）")
    total_score = Column(Integer, nullable=False, default=100)
    pass_score = Column(Integer, nullable=False, default=60)
    is_published = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=True, comment="考试开始时间")
    end_time = Column(DateTime, nullable=True, comment="考试结束时间")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", backref="created_exams")
    questions = relationship("ExamQuestion", backref="exam", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exam {self.title}>"


class ExamQuestion(Base):
    """考试题目表"""
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_type = Column(String(20), nullable=False, comment="single_choice/multiple_choice/true_false/short_answer/code")
    content = Column(Text, nullable=False)
    options = Column(Text, nullable=True, comment="选项JSON格式")
    correct_answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=False)
    analysis = Column(Text, nullable=True, comment="答案解析")
    sort_order = Column(Integer, default=0)
    test_cases = Column(Text, nullable=True, comment="测试用例JSON格式，代码题用")

    answers = relationship("ExamAnswer", backref="question")

    def __repr__(self):
        return f"<ExamQuestion {self.id} exam:{self.exam_id} type:{self.question_type}>"


class ExamAttempt(Base):
    """考试尝试记录表"""
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    is_passed = Column(Boolean, nullable=True)
    status = Column(String(20), default="in_progress", comment="in_progress/submitted/graded")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="exam_attempts")
    exam = relationship("Exam", backref="attempts")
    answers = relationship("ExamAnswer", backref="attempt", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExamAttempt {self.id} exam:{self.exam_id} user:{self.user_id} status:{self.status}>"


class ExamAnswer(Base):
    """考试答案表"""
    __tablename__ = "exam_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("exam_questions.id"), nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    score = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ExamAnswer {self.id} attempt:{self.attempt_id} q:{self.question_id}>"


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(80), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon = Column(String(50))
    category = Column(String(50))
    threshold = Column(Integer, default=1)
    exp_reward = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Integer, default=1)


class DailyCheckin(Base):
    """每日签到表"""
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkin_date = Column(DateTime, nullable=False)
    streak_count = Column(Integer, default=1)
    exp_earned = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExerciseSubmissionRecord(Base):
    """习题提交记录表"""
    __tablename__ = "exercise_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    code = Column(Text, nullable=True)
    result = Column(String(20), default="fail")
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    """学习笔记表"""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIConfig(Base):
    """AI大模型配置表"""
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    provider = Column(String(50), nullable=False, comment="提供商: minimax/openai/ark/custom")
    api_key = Column(Text, nullable=False, comment="API密钥(加密存储)")
    base_url = Column(String(500), nullable=True, comment="API基础URL")
    model = Column(String(200), nullable=False, comment="模型名称")
    is_active = Column(Boolean, default=False, comment="是否为当前激活配置")
    max_tokens = Column(Integer, default=2000, comment="最大token数")
    temperature = Column(Float, default=0.7, comment="温度参数")
    timeout_seconds = Column(Integer, default=60, comment="超时时间(秒)")
    group_id = Column(String(100), nullable=True, comment="MiniMax Group ID")
    quota_total = Column(Integer, nullable=True, comment="总额度")
    quota_used = Column(Integer, nullable=True, comment="已用额度")
    quota_updated_at = Column(DateTime, nullable=True, comment="额度更新时间")
    last_test_at = Column(DateTime, nullable=True, comment="最后测试时间")
    last_test_result = Column(String(20), nullable=True, comment="最后测试结果: success/failed")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
