"""
数据模型 - 与实际数据库表名和列名匹配
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Date,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from fastapi_backend.core.database import Base


class User(Base):
    """Frontend user model mapped to the legacy Flask users table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_super_admin = Column(Boolean, default=False)
    # RBAC: 关联角色（为 NULL 时回退到 is_admin 判断）
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联角色ID",
    )
    level = Column(Integer, default=1)
    score = Column(Integer, default=0)
    assessment_score = Column(Integer, nullable=True)
    study_time = Column(Integer, default=0)
    avatar = Column(String(500))

    # RBAC 关联
    role_obj = relationship("Role", back_populates="users")
    # 多角色关联（与 role_id 单角色并存，向后兼容）
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

    @property
    def role(self) -> str:
        """用户角色：优先从 role_obj 获取，回退到 is_admin 字段"""
        if self.role_obj:
            return self.role_obj.name
        return "admin" if self.is_admin else "user"

    @property
    def permissions(self) -> list:
        """获取用户所有权限代码列表"""
        try:
            if self.role_obj:
                return [p.code for p in self.role_obj.permissions]
        except Exception:
            pass
        # 向后兼容：旧管理员拥有所有权限
        if self.is_admin:
            return ["*"]
        return []

    def __repr__(self):
        return f"<User {self.username}>"


class ApiGroup(Base):
    """接口分组表 - 支持树形层级结构"""

    __tablename__ = "auto_test_groups"

    id = Column(Integer, primary_key=True, index=True, comment="分组ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="分组名称")
    description = Column(String(500), nullable=True, comment="分组描述")
    parent_id = Column(
        Integer,
        ForeignKey("auto_test_groups.id"),
        nullable=True,
        comment="父分组ID，顶级分组为NULL",
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    # 自关联关系
    children = relationship("ApiGroup", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<ApiGroup {self.name}>"


class ApiCase(Base):
    """接口用例表"""

    __tablename__ = "interface_test_cases"

    id = Column(Integer, primary_key=True, index=True, comment="用例ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    folder_id = Column(
        Integer,
        ForeignKey("interface_test_folders.id"),
        nullable=True,
        comment="所属目录ID",
    )
    name = Column(String(200), nullable=False, comment="用例名称")
    description = Column(Text, nullable=True, comment="描述")
    url = Column(String(2000), nullable=False, comment="接口地址")
    method = Column(String(10), nullable=False, comment="请求方法: GET/POST/PUT/DELETE/PATCH")
    headers = Column(Text, nullable=True, comment="请求头 JSON 格式")
    body = Column(Text, nullable=True, comment="请求体 JSON/表单格式")
    body_type = Column(String(20), default="json", comment="请求体类型: json/form/text")
    is_public = Column(Boolean, default=False, comment="是否公开")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )


class Environment(Base):
    """测试环境表"""

    __tablename__ = "interface_test_environments"

    id = Column(Integer, primary_key=True, index=True, comment="环境ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="环境名称")
    base_url = Column(String(500), nullable=True, comment="基础URL")
    variables = Column(Text, nullable=True, comment="环境变量 JSON 格式")
    is_default = Column(Boolean, default=False, comment="是否默认环境")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

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
    environment_id = Column(
        Integer,
        ForeignKey("interface_test_environments.id"),
        nullable=True,
        comment="测试环境ID",
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    def __repr__(self):
        return f"<TestPlan {self.name}>"


class TestReport(Base):
    """测试报告表"""

    __tablename__ = "interface_test_reports"

    id = Column(Integer, primary_key=True, index=True, comment="报告ID")
    plan_id = Column(
        Integer,
        ForeignKey("interface_test_plans.id"),
        nullable=True,
        comment="所属计划ID",
    )
    plan_name = Column(String(200), nullable=True, comment="计划名称快照")
    total_count = Column(Integer, default=0, comment="总用例数")
    success_count = Column(Integer, default=0, comment="成功数")
    failed_count = Column(Integer, default=0, comment="失败数")
    total_time = Column(Integer, default=0, comment="总耗时 毫秒")
    status = Column(String(20), default="pending", comment="状态: pending/running/completed/failed")
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="执行时间")

    # 关联
    results = relationship("TestReportResult", backref="report", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestReport {self.id} {self.plan_name}>"


class TestReportResult(Base):
    """测试结果表 - 单个用例执行结果"""

    __tablename__ = "interface_test_report_results"

    id = Column(Integer, primary_key=True, index=True, comment="结果ID")
    report_id = Column(
        Integer,
        ForeignKey("interface_test_reports.id"),
        nullable=False,
        comment="所属报告ID",
    )
    case_id = Column(
        Integer,
        ForeignKey("interface_test_cases.id"),
        nullable=True,
        comment="执行用例ID",
    )
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
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="执行时间")

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
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=True, comment="关联学习路径ID")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    __table_args__ = (
        Index("idx_iq_difficulty_published", "difficulty", "is_published"),
        Index("idx_iq_category", "category"),
        Index("idx_iq_learning_path", "learning_path_id"),
    )

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
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间（旧字段）")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="结束时间（旧字段）")
    feedback = Column(Text, nullable=True, comment="反馈（旧字段）")
    improvement_suggestions = Column(Text, nullable=True, comment="改进建议（旧字段）")
    # FastAPI 新字段
    question_id = Column(
        Integer,
        nullable=True,
        comment="题目ID（可能是InterviewQuestion或Exercise的ID）",
    )
    status = Column(
        String(20),
        default="started",
        comment="状态: started/submitted/finished/abandoned",
    )
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="开始时间")
    finished_at = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    latest_score = Column(Integer, nullable=True, comment="最新成绩 (0-100)")
    latest_submission_id = Column(
        Integer,
        ForeignKey("submissions.id", use_alter=True),
        nullable=True,
        comment="最新提交记录ID",
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    # 关联关系
    user = relationship("User", backref="interview_sessions")
    latest_submission = relationship("Submission", foreign_keys=[latest_submission_id], post_update=True)

    __table_args__ = (Index("idx_interview_session_user_status", "user_id", "status"),)

    def __repr__(self):
        return f"<InterviewSession {self.id} user:{self.user_id} question:{self.question_id} status:{self.status}>"


class Submission(Base):
    """代码提交记录表"""

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True, comment="提交ID")
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, comment="会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    question_id = Column(
        Integer,
        nullable=False,
        comment="题目ID（可能是InterviewQuestion或Exercise的ID）",
    )
    question_source = Column(
        String(20),
        default="interview_question",
        comment="题目来源: interview_question / exercise",
    )
    language = Column(String(20), default="python", comment="编程语言")
    source_code = Column(Text, nullable=False, comment="源代码")
    execution_status = Column(
        String(20),
        default="pending",
        comment="执行状态: pending/running/success/failed",
    )
    ai_evaluation_status = Column(
        String(20),
        default="pending",
        comment="AI评估状态: pending/running/completed/failed",
    )
    score = Column(Integer, nullable=True, comment="AI评分 (0-100)")
    feedback = Column(Text, nullable=True, comment="AI反馈")
    feedback_json = Column(
        Text, nullable=True, comment="AI结构化反馈 JSON: {score, feedback, strengths[], weaknesses[], suggestion}"
    )
    execution_result = Column(Text, nullable=True, comment="执行结果 JSON 格式")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    # 关联关系
    session = relationship("InterviewSession", backref="submissions", foreign_keys=[session_id])
    user = relationship("User", backref="submissions", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_submission_user_created", "user_id", "created_at"),
        Index("idx_submission_user_status", "user_id", "execution_status"),
    )

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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_id = Column(Integer, nullable=True)

    # Relationships
    exercises = relationship("Exercise", backref="learning_path", lazy="selectin")
    creator = relationship("User", foreign_keys=[user_id], backref="learning_paths")
    lesson_sections = relationship("LessonSection", back_populates="learning_path", lazy="selectin")

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
    hint = Column(Text, nullable=True, comment="提示信息")
    setup_sql = Column(Text, nullable=True, comment="SQL题建表和初始数据")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_id = Column(Integer, nullable=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[user_id], backref="exercises")

    __table_args__ = (
        Index("idx_exercise_language_public", "language", "is_public"),
        Index("idx_exercise_user_id", "user_id"),
        Index("idx_exercise_learning_path", "learning_path_id"),
    )

    def __repr__(self):
        return f"<Exercise {self.title}>"


class LessonSection(Base):
    """课程章节表 - 存储学习路径的实际教程正文"""

    __tablename__ = "lesson_sections"

    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, comment="教程正文(Markdown格式)")
    sort_order = Column(Integer, default=0)
    knowledge_point = Column(String(200))
    time_estimate = Column(Integer, default=15, comment="预计学习时间(分钟)")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    learning_path = relationship("LearningPath", back_populates="lesson_sections")

    def __repr__(self):
        return f"<LessonSection {self.title}>"


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
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_progress_user_exercise", "user_id", "exercise_id", unique=True),
        Index("idx_progress_user_completed", "user_id", "completed"),
    )


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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", backref="posts")

    __table_args__ = (
        Index("idx_post_category_top_essence", "category", "is_top", "is_essence"),
        Index("idx_post_user_id", "user_id"),
    )


class Comment(Base):
    """社区评论表"""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"))

    user = relationship("User", backref="comments")
    post = relationship("Post", backref=backref("comments", cascade="all, delete-orphan"))
    parent = relationship("Comment", remote_side=[id], backref="replies")

    __table_args__ = (
        Index("idx_comment_user_id", "user_id"),
        Index("idx_comment_post_id", "post_id"),
    )


class Like(Base):
    """点赞表"""

    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"))
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="likes")
    post = relationship("Post", backref="likes")
    comment = relationship("Comment", backref="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_likes_user_post"),
        UniqueConstraint("user_id", "comment_id", name="uq_likes_user_comment"),
        Index("uq_likes_user_post_not_null", "user_id", "post_id", unique=True, postgresql_where=post_id.isnot(None)),
        Index(
            "uq_likes_user_comment_not_null",
            "user_id",
            "comment_id",
            unique=True,
            postgresql_where=comment_id.isnot(None),
        ),
    )


class Favorite(Base):
    """收藏表 - 支持帖子/习题/笔记"""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=True)
    item_type = Column(
        String(20),
        nullable=False,
        default="post",
        comment="收藏类型: post/exercise/note",
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="favorites")
    post = relationship("Post", backref="favorites")
    exercise = relationship("Exercise")
    note = relationship("Note")

    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_favorites_user_exercise"),
        UniqueConstraint("user_id", "post_id", name="uq_favorites_user_post"),
        Index("idx_favorite_user_id", "user_id"),
        Index("idx_favorite_item_type", "user_id", "item_type"),
    )


class LearningPathCollection(Base):
    """学习路径收藏表 - 记录用户对学习路径的收藏关系"""

    __tablename__ = "learning_path_collections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="learning_path_collections")
    learning_path = relationship("LearningPath", backref="collections")

    __table_args__ = (
        UniqueConstraint("user_id", "learning_path_id", name="uq_learning_path_collection_user_path"),
        Index("idx_learning_path_collection_user_id", "user_id"),
    )


class TestCase(Base):
    """面试题测试用例表"""

    __tablename__ = "interview_test_cases"

    id = Column(Integer, primary_key=True, index=True, comment="测试用例ID")
    question_id = Column(
        Integer,
        ForeignKey("interview_questions.id"),
        nullable=False,
        comment="关联题目ID",
    )
    input = Column(Text, nullable=False, comment="输入数据")
    expected_output = Column(Text, nullable=False, comment="预期输出")
    is_example = Column(Boolean, default=False, comment="是否为示例用例（用户可见）")
    is_hidden = Column(Boolean, default=False, comment="是否为隐藏用例（用户不可见，用于判题）")
    description = Column(Text, nullable=True, comment="用例描述")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

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
    start_time = Column(DateTime(timezone=True), nullable=True, comment="考试开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="考试结束时间")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", backref="created_exams")
    questions = relationship("ExamQuestion", backref="exam", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_exam_type_published", "exam_type", "is_published"),
        Index("idx_exam_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<Exam {self.title}>"


class ExamQuestion(Base):
    """考试题目表"""

    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_type = Column(
        String(20),
        nullable=False,
        comment="single_choice/multiple_choice/true_false/short_answer/code",
    )
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
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=True)
    score = Column(Integer, nullable=True)
    is_passed = Column(Boolean, nullable=True)
    status = Column(String(20), default="in_progress", comment="in_progress/submitted/graded")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="exam_attempts")
    exam = relationship("Exam", backref="attempts")
    answers = relationship("ExamAnswer", backref="attempt", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_exam_attempt_user_status", "user_id", "status"),
        Index("idx_exam_attempt_exam_id", "exam_id"),
    )

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

    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_exam_answer_attempt_question"),)

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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    progress = Column(Integer, default=1)

    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)


class DailyCheckin(Base):
    """每日签到表"""

    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkin_date = Column(Date, nullable=False)
    streak_count = Column(Integer, default=1)
    exp_earned = Column(Integer, default=5)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "checkin_date", name="uq_checkin_user_date"),)


class ExerciseSubmissionRecord(Base):
    """习题提交记录表"""

    __tablename__ = "exercise_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    code = Column(Text, nullable=True)
    result = Column(String(20), default="fail")
    score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_exercise_sub_user_created", "user_id", "created_at"),
        Index("idx_exercise_sub_user_exercise", "user_id", "exercise_id"),
    )


class Note(Base):
    """学习笔记表"""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


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
    quota_updated_at = Column(DateTime(timezone=True), nullable=True, comment="额度更新时间")
    last_test_at = Column(DateTime(timezone=True), nullable=True, comment="最后测试时间")
    last_test_result = Column(String(20), nullable=True, comment="最后测试结果: success/failed")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ============ RBAC 权限模型 ============


class Role(Base):
    """角色表"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="角色标识: admin/tester/viewer")
    code = Column(
        String(50),
        unique=True,
        nullable=True,
        comment="角色代码(大写唯一): ADMIN/TESTER/VIEWER，为空时回退到 name",
    )
    display_name = Column(String(100), nullable=False, comment="角色显示名称")
    description = Column(Text, nullable=True, comment="角色描述")
    is_system = Column(Boolean, default=False, comment="是否为系统内置角色（不可删除）")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    users = relationship("User", back_populates="role_obj")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    user_assignments = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """权限表"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, comment="权限代码: exercise:create")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(Text, nullable=True, comment="权限描述")
    module = Column(String(50), nullable=False, comment="所属模块: exercise/user/exam等")
    action = Column(
        String(50),
        nullable=True,
        comment="操作类型: create/read/update/delete/execute/import/export",
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class RolePermissionMapping(Base):
    """角色-权限关联表（多对多）"""

    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("idx_rbac_role_perm", "role_id", "permission_id", unique=True),)


class UserRole(Base):
    """用户-角色关联表（多对多，支持一个用户拥有多个角色）

    与 User.role_id（单角色，向后兼容）并存：
    - 权限聚合时同时考虑 role_id 指向的角色与本表中的所有角色。
    - assigned_by 记录分配者 user_id，便于审计。
    """

    __tablename__ = "user_roles"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID",
    )
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="角色ID",
    )
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    assigned_by = Column(Integer, nullable=True, comment="分配者 user_id")

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_assignments")

    def __repr__(self):
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"


class TokenBlacklist(Base):
    """Token 黑名单表 - 持久化吊销的 JWT token"""

    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="token 的 SHA256 哈希",
    )
    token_type = Column(String(20), default="access", comment="token 类型: access/refresh")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联用户ID",
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="token 原始过期时间")
    blacklisted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="加入黑名单时间",
    )

    __table_args__ = (
        Index("idx_token_blacklist_hash", "token_hash"),
        Index("idx_token_blacklist_expires", "expires_at"),
    )


# ========== 测试项目实战空间模型 ==========


class ProjectSpace(Base):
    """项目实战空间表"""

    __tablename__ = "project_spaces"

    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(
        Integer,
        ForeignKey("learning_paths.id"),
        nullable=False,
        comment="所属学习路径ID",
    )
    title = Column(String(200), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    overview = Column(Text, nullable=True, comment="项目概述(背景/目标)")
    difficulty = Column(String(20), default="medium", comment="难度: easy/medium/hard")
    status = Column(String(20), default="draft", comment="状态: draft/published/archived")
    estimated_hours = Column(Integer, default=8, comment="预计完成时间(小时)")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    learning_path = relationship("LearningPath", backref="project_spaces")
    tasks = relationship(
        "ProjectTask",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectTask.sort_order",
    )
    resources = relationship(
        "ProjectResource",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectResource.sort_order",
    )
    submissions = relationship("ProjectSubmission", back_populates="project", cascade="all, delete-orphan")
    evaluations = relationship("ProjectEvaluation", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProjectSpace {self.title}>"


class ProjectTask(Base):
    """项目任务表"""

    __tablename__ = "project_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_spaces.id"), nullable=False, comment="所属项目ID")
    title = Column(String(200), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    task_type = Column(
        String(50),
        nullable=False,
        comment="任务类型: test_point_design/test_case_design/api_debug/auto_execution/defect_analysis/project_summary",
    )
    requirements = Column(Text, nullable=True, comment="任务要求")
    hints = Column(Text, nullable=True, comment="提示/参考资料")
    score = Column(Integer, default=10, comment="任务分值")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("ProjectSpace", back_populates="tasks")
    submissions = relationship("ProjectSubmission", back_populates="task")

    TASK_TYPE_LABELS = {
        "test_point_design": "测试点设计",
        "test_case_design": "测试用例设计",
        "api_debug": "接口调试",
        "auto_execution": "自动化执行",
        "defect_analysis": "缺陷分析",
        "project_summary": "项目总结",
    }

    def __repr__(self):
        return f"<ProjectTask {self.title}>"


class ProjectResource(Base):
    """项目资料表"""

    __tablename__ = "project_resources"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_spaces.id"), nullable=False, comment="所属项目ID")
    title = Column(String(200), nullable=False, comment="资料名称")
    resource_type = Column(
        String(50),
        default="document",
        comment="资料类型: document/api_doc/test_data/reference/link",
    )
    content = Column(Text, nullable=True, comment="内容(Markdown)")
    url = Column(Text, nullable=True, comment="外部链接")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("ProjectSpace", back_populates="resources")

    RESOURCE_TYPE_LABELS = {
        "document": "项目文档",
        "api_doc": "接口文档",
        "test_data": "测试数据",
        "reference": "参考资料",
        "link": "外部链接",
    }

    def __repr__(self):
        return f"<ProjectResource {self.title}>"


class ProjectSubmission(Base):
    """项目提交记录表"""

    __tablename__ = "project_submissions"
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_submission_user_task"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_spaces.id"), nullable=False, comment="所属项目ID")
    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False, comment="所属任务ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="提交用户ID")
    content = Column(Text, nullable=True, comment="提交内容")
    attachments = Column(Text, nullable=True, comment="附件JSON")
    status = Column(
        String(20),
        default="submitted",
        comment="状态: submitted/reviewed/accepted/rejected",
    )
    score = Column(Integer, nullable=True, comment="评分")
    feedback = Column(Text, nullable=True, comment="反馈")
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("ProjectSpace", back_populates="submissions")
    task = relationship("ProjectTask", back_populates="submissions")
    user = relationship("User", backref="project_submissions")

    def __repr__(self):
        return f"<ProjectSubmission {self.id} task:{self.task_id}>"


class ProjectEvaluation(Base):
    """项目验收评价表"""

    __tablename__ = "project_evaluations"
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_evaluation_user_project"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_spaces.id"), nullable=False, comment="所属项目ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="评价用户ID")
    total_score = Column(Integer, default=0, comment="总分")
    task_scores = Column(Text, nullable=True, comment="各任务得分JSON")
    comment = Column(Text, nullable=True, comment="总评语")
    strengths = Column(Text, nullable=True, comment="优点")
    improvements = Column(Text, nullable=True, comment="改进建议")
    is_passed = Column(Boolean, default=False, comment="是否通过")
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("ProjectSpace", back_populates="evaluations")
    user = relationship("User", backref="project_evaluations")

    def __repr__(self):
        return f"<ProjectEvaluation {self.id} project:{self.project_id}>"


# ========== 通知系统 ==========

NOTIFICATION_TYPES = {
    "reply": "新回复",
    "exam_start": "考试开始",
    "exam_deadline": "考试截止",
    "project_feedback": "项目反馈",
    "achievement": "获得成就",
    "system": "系统公告",
    "learning_reminder": "学习提醒",
}


class Notification(Base):
    """通知表"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="接收用户ID")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=True, comment="通知内容")
    type = Column(String(30), default="system", comment="通知类型")
    link = Column(String(500), nullable=True, comment="跳转链接")
    is_read = Column(Boolean, default=False, comment="是否已读")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="notifications")

    __table_args__ = (
        Index("idx_notification_user_read", "user_id", "is_read"),
        Index("idx_notification_type", "type"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "type": self.type,
            "type_label": NOTIFICATION_TYPES.get(self.type, self.type),
            "link": self.link,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIPointsConfig(Base):
    """AI 功能积分消耗配置"""

    __tablename__ = "ai_points_config"

    id = Column(Integer, primary_key=True, index=True)
    feature = Column(String(50), unique=True, nullable=False, comment="功能标识")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    points_cost = Column(Integer, nullable=False, default=1, comment="积分消耗")
    description = Column(String(255), nullable=True, comment="功能说明")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class PointsTransaction(Base):
    """积分流水账本 — 记录每一笔积分变动"""

    __tablename__ = "points_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False, comment="变动数量（正数=收入，负数=支出）")
    balance_after = Column(Integer, nullable=False, comment="变动后余额")
    tx_type = Column(
        String(30),
        nullable=False,
        index=True,
        comment="类型: checkin/project/purchase/admin_grant/admin_deduct/ai_usage/refund",
    )
    source = Column(String(100), nullable=True, comment="来源描述")
    related_feature = Column(String(50), nullable=True, comment="关联的AI功能标识")
    note = Column(String(255), nullable=True, comment="备注")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="points_transactions")

    __table_args__ = (
        Index("idx_ptx_user_type", "user_id", "tx_type"),
        Index("idx_ptx_created", "created_at"),
    )


class AIUsageLog(Base):
    """AI 功能使用日志 — 记录每次 AI 调用"""

    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    feature = Column(String(50), nullable=False, index=True, comment="功能标识")
    points_cost = Column(Integer, nullable=False, comment="扣除的积分")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="ai_usage_logs")

    __table_args__ = (
        Index("idx_ai_usage_user_feature", "user_id", "feature"),
        Index("idx_ai_usage_created", "created_at"),
    )


class AuditLog(Base):
    """操作审计日志表（记录用户对关键资源的操作，兼容原有高危操作审计）"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作用户ID")
    admin_id = Column(Integer, nullable=True, comment="管理员ID(兼容字段)")
    username = Column(String(80), nullable=True, comment="操作者用户名(冗余存储,便于查询)")
    action = Column(String(200), nullable=False, comment="操作类型/描述: create/update/delete/execute/import/export 或具体描述")
    action_type = Column(
        String(50), nullable=False, default="other", comment="操作分类: backup/user_management/system/other(兼容字段)"
    )
    resource_type = Column(String(50), nullable=True, comment="资源类型: case/scenario/suite/environment/variable/mock_rule/db_connection/schedule")
    resource_id = Column(Integer, nullable=True, comment="资源ID")
    resource_name = Column(String(500), nullable=True, comment="资源名称(冗余存储)")
    detail = Column(Text, nullable=True, comment="变更详情(JSON字符串,记录before/after)")
    ip_address = Column(String(100), nullable=True, comment="操作IP地址")
    user_agent = Column(String(500), nullable=True, comment="User-Agent")
    request_path = Column(String(500), nullable=True, comment="请求路径")
    request_method = Column(String(10), nullable=True, comment="HTTP方法")
    status = Column(String(20), nullable=True, default="success", comment="操作状态: success/failed")
    error_message = Column(Text, nullable=True, comment="失败原因")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="操作时间")

    user = relationship("User", backref="audit_logs", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_action_type", "action_type"),
        Index("idx_audit_logs_user_created", "user_id", "created_at"),
        Index("idx_audit_logs_resource_created", "resource_type", "resource_id", "created_at"),
        Index("idx_audit_logs_action_created", "action", "created_at"),
    )
