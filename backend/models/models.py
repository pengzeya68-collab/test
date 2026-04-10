# Database models for TestMasterProject
import uuid
from datetime import datetime
from ..extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True)  # 手机号，用于找回密码
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # 是否为管理员
    is_super_admin = db.Column(db.Boolean, default=False)  # 是否为超级管理员
    level = db.Column(db.Integer, default=1)  # 用户等级 1-4
    score = db.Column(db.Integer, default=0)  # 积分
    study_time = db.Column(db.Integer, default=0)  # 学习时长（分钟）
    avatar = db.Column(db.String(500))  # 头像URL



# 独立管理员表
class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, comment='管理员账号')
    password_hash = db.Column(db.String(128), nullable=False, comment='密码')
    name = db.Column(db.String(80), comment='真实姓名')
    email = db.Column(db.String(120), comment='邮箱')
    avatar = db.Column(db.String(500), comment='头像')
    role = db.Column(db.String(20), default='admin', comment='角色: super_admin, admin, editor')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    last_login_at = db.Column(db.DateTime, comment='最后登录时间')
    last_login_ip = db.Column(db.String(50), comment='最后登录IP')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def check_password(self, password):
        """验证密码"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'
    
    # Relationships

class LearningPath(db.Model):
    __tablename__ = 'learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)  # 路径简介
    learning_objectives = db.Column(db.Text)  # 学习目标
    knowledge_outline = db.Column(db.Text)  # 知识点大纲，JSON格式或Markdown
    supporting_resources = db.Column(db.Text)  # 配套学习资源
    prerequisites = db.Column(db.String(500))  # 前置要求
    language = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    stage = db.Column(db.Integer, default=1)  # 1-5 对应5个学习阶段
    estimated_hours = db.Column(db.Integer, default=10)
    exercise_count = db.Column(db.Integer, default=0)  # 配套习题数量
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys - 前台用户创建的路径关联到users表，后台管理员创建的也可以关联到admin_users表
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    
    # Relationships
    exercises = db.relationship('Exercise', backref='learning_path', lazy=True)
    creator = db.relationship('User', foreign_keys=[user_id], backref='learning_paths')
    admin_creator = db.relationship('AdminUser', foreign_keys=[admin_id], backref='created_paths')
    
    def __repr__(self):
        return f'<LearningPath {self.title}>'

class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    solution = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='easy')  # easy, medium, hard
    language = db.Column(db.String(50), nullable=False)  # 通用/Python/SQL/Shell
    module = db.Column(db.String(50), default='normal')  # 模块: normal/automation/api 普通习题/自动化测试/接口测试
    category = db.Column(db.String(100))  # e.g., 'variables', 'functions', 'oop'
    stage = db.Column(db.Integer, default=1)  # 1-5 对应5个学习阶段
    knowledge_point = db.Column(db.String(200))  # 所属知识点
    time_estimate = db.Column(db.Integer)  # in minutes
    is_public = db.Column(db.Boolean, default=True)
    exercise_type = db.Column(db.String(20), default='text')  # text/code/multiple_choice
    test_cases = db.Column(db.Text)  # JSON格式的测试用例，用于代码判题
    code_template = db.Column(db.Text)  # 代码模板，用户打开时默认显示
    expected_output = db.Column(db.Text)  # 预期输出
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    learning_path_id = db.Column(db.Integer, db.ForeignKey('learning_paths.id'))
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[user_id], backref='exercises')
    admin_creator = db.relationship('AdminUser', foreign_keys=[admin_id], backref='created_exercises')
    
    def __repr__(self):
        return f'<Exercise {self.title}>'

# Additional models can be added here
class Progress(db.Model):
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)  # 0-100
    time_spent = db.Column(db.Integer)  # in seconds
    attempts = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('progress_records', lazy=True))
    exercise = db.relationship('Exercise', backref=db.backref('progress_records', lazy=True))
    
    def __repr__(self):
        return f'<Progress User:{self.user_id} Exercise:{self.exercise_id}>'


class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))  # 摘要
    tags = db.Column(db.String(200))  # 标签，逗号分隔
    category = db.Column(db.String(50), nullable=False)  # 分类：经验分享/问题求助/资源分享/求职交流
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    is_essence = db.Column(db.Boolean, default=False)  # 是否精华帖
    is_top = db.Column(db.Boolean, default=False)  # 是否置顶
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 关联
    user = db.relationship('User', backref=db.backref('posts', lazy=True))


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))  # 父评论ID，用于回复
    
    # 关联
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    post = db.relationship('Post', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan'))
    parent = db.relationship('Comment', remote_side=[id], backref=db.backref('replies', lazy=True))


class Like(db.Model):
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 确保用户不能重复点赞
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
        db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),
    )


class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 确保用户不能重复收藏
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_favorite'),
    )


class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    exam_type = db.Column(db.String(50), nullable=False)  # 模拟考试/正式考试/专项练习
    difficulty = db.Column(db.String(20), default='medium')  # easy/medium/hard
    duration = db.Column(db.Integer, nullable=False)  # 考试时长（分钟）
    total_score = db.Column(db.Integer, nullable=False, default=100)
    pass_score = db.Column(db.Integer, nullable=False, default=60)
    is_published = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime)  # 考试开始时间
    end_time = db.Column(db.DateTime)  # 考试结束时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 关联
    user = db.relationship('User', backref=db.backref('created_exams', lazy=True))
    questions = db.relationship('ExamQuestion', backref='exam', lazy=True, cascade='all, delete-orphan')


class ExamQuestion(db.Model):
    __tablename__ = 'exam_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # single_choice/multiple_choice/true_false/short_answer/code
    content = db.Column(db.Text, nullable=False)  # 题目内容
    options = db.Column(db.Text)  # 选项（JSON格式，选择题用）
    correct_answer = db.Column(db.Text)  # 正确答案
    score = db.Column(db.Integer, nullable=False)  # 题目分数
    analysis = db.Column(db.Text)  # 答案解析
    sort_order = db.Column(db.Integer, default=0)  # 题目排序


class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    is_passed = db.Column(db.Boolean)
    status = db.Column(db.String(20), default='in_progress')  # in_progress/submitted/graded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('exam_attempts', lazy=True))
    exam = db.relationship('Exam', backref=db.backref('attempts', lazy=True))
    answers = db.relationship('ExamAnswer', backref='attempt', lazy=True, cascade='all, delete-orphan')


class ExamAnswer(db.Model):
    __tablename__ = 'exam_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('exam_questions.id'), nullable=False)
    user_answer = db.Column(db.Text)  # 用户答案
    is_correct = db.Column(db.Boolean)  # 是否正确
    score = db.Column(db.Integer)  # 得分
    feedback = db.Column(db.Text)  # 评分反馈
    
    # 关联
    question = db.relationship('ExamQuestion', backref=db.backref('answers', lazy=True))


class InterviewQuestion(db.Model):
    __tablename__ = 'interview_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)  # 问题
    content = db.Column(db.Text)  # 问题补充描述
    answer = db.Column(db.Text, nullable=False)  # 参考答案
    category = db.Column(db.String(50), nullable=False)  # 分类：基础测试/自动化测试/性能测试/数据库/编程/HR面
    difficulty = db.Column(db.String(20), default='medium')  # easy/medium/hard
    position_level = db.Column(db.String(50))  # 适用岗位：初级/中级/高级/专家
    tags = db.Column(db.String(200))  # 标签，逗号分隔
    company = db.Column(db.String(100))  # 来源公司
    view_count = db.Column(db.Integer, default=0)  # 浏览次数
    collect_count = db.Column(db.Integer, default=0)  # 收藏次数
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InterviewSession(db.Model):
    __tablename__ = 'interview_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(100), nullable=False)  # 应聘岗位
    level = db.Column(db.String(50), nullable=False)  # 级别
    interview_type = db.Column(db.String(50), nullable=False)  # 技术面/HR面/群面
    total_score = db.Column(db.Integer, default=100)
    user_score = db.Column(db.Integer)
    status = db.Column(db.String(20), default='in_progress')  # in_progress/completed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    feedback = db.Column(db.Text)  # 总体评价
    improvement_suggestions = db.Column(db.Text)  # 改进建议
    
    # 关联
    user = db.relationship('User', backref=db.backref('interview_sessions', lazy=True))
    questions = db.relationship('InterviewQuestionRecord', backref='session', lazy=True, cascade='all, delete-orphan')


class InterviewQuestionRecord(db.Model):
    __tablename__ = 'interview_question_records'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('interview_questions.id'), nullable=False)
    user_answer = db.Column(db.Text)  # 用户回答
    ai_feedback = db.Column(db.Text)  # AI点评
    score = db.Column(db.Integer)  # 得分（0-10）
    is_answered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    question = db.relationship('InterviewQuestion', backref=db.backref('records', lazy=True))


class InterviewQuestionCollection(db.Model):
    __tablename__ = 'interview_question_collections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('interview_questions.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 确保用户不能重复收藏
    __table_args__ = (
        db.UniqueConstraint('user_id', 'question_id', name='unique_user_interview_question'),
    )


# 接口测试文件夹
class InterfaceTestFolder(db.Model):
    __tablename__ = 'interface_test_folders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('interface_test_folders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('interface_test_folders', lazy=True))
    parent = db.relationship('InterfaceTestFolder', remote_side=[id], backref=db.backref('children', lazy=True))


# 接口测试环境
class InterfaceTestEnvironment(db.Model):
    __tablename__ = 'interface_test_environments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # 环境名称：开发/测试/生产
    base_url = db.Column(db.String(2000), nullable=False)  # 基础URL
    variables = db.Column(db.Text)  # JSON格式存储环境变量 {key: value}
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('interface_test_environments', lazy=True))


class InterfaceTestCase(db.Model):
    __tablename__ = 'interface_test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('interface_test_folders.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)  # 用例名称
    description = db.Column(db.Text)  # 用例描述
    url = db.Column(db.String(2000), nullable=False)  # 请求URL
    method = db.Column(db.String(10), nullable=False, default='GET')  # GET/POST/PUT/DELETE等
    headers = db.Column(db.Text)  # JSON格式存储请求头
    body = db.Column(db.Text)  # 请求体
    body_type = db.Column(db.String(20), default='json')  # json/form/text/form-data
    is_public = db.Column(db.Boolean, default=False)  # 是否公开
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('interface_test_cases', lazy=True))
    folder = db.relationship('InterfaceTestFolder', backref=db.backref('cases', lazy=True))


# 接口测试计划（保存自定义执行顺序的测试计划）
class InterfaceTestPlan(db.Model):
    __tablename__ = 'interface_test_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # 计划名称
    description = db.Column(db.Text)  # 计划描述
    case_ids = db.Column(db.Text, nullable=False)  # JSON格式存储用例ID列表，按执行顺序保存
    environment_id = db.Column(db.Integer, db.ForeignKey('interface_test_environments.id'), nullable=True)  # 使用的环境
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('interface_test_plans', lazy=True))
    environment = db.relationship('InterfaceTestEnvironment', backref=db.backref('plans', lazy=True))


# 接口测试报告
class InterfaceTestReport(db.Model):
    __tablename__ = 'interface_test_reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('interface_test_plans.id'), nullable=True)
    plan_name = db.Column(db.String(200))  # 保存计划名称快照
    total_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)  # 毫秒
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('interface_test_reports', lazy=True))
    plan = db.relationship('InterfaceTestPlan', backref=db.backref('reports', lazy=True))
    results = db.relationship('InterfaceTestReportResult', backref='report', lazy=True, cascade='all, delete-orphan')


# 接口测试报告结果
class InterfaceTestReportResult(db.Model):
    __tablename__ = 'interface_test_report_results'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('interface_test_reports.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('interface_test_cases.id'), nullable=True)
    case_name = db.Column(db.String(200))
    method = db.Column(db.String(10))
    url = db.Column(db.String(2000))
    status_code = db.Column(db.Integer)
    success = db.Column(db.Boolean, default=False)
    time = db.Column(db.Integer, default=0)  # 毫秒
    error = db.Column(db.Text)
    request_headers = db.Column(db.Text)
    request_body = db.Column(db.Text)
    response = db.Column(db.Text)
    response_headers = db.Column(db.Text)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    case = db.relationship('InterfaceTestCase', backref=db.backref('report_results', lazy=True))


# ========== 零代码自动化测试 =============
# 自动化测试分组（树形结构
class AutoTestGroup(db.Model):
    __tablename__ = 'auto_test_groups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # 分组名称
    description = db.Column(db.Text)  # 分组描述
    parent_id = db.Column(db.Integer, db.ForeignKey('auto_test_groups.id'), nullable=True)  # 父分组ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('auto_test_groups', lazy=True))
    parent = db.relationship('AutoTestGroup', remote_side=[id], backref=db.backref('children', lazy=True))

    @property
    def case_count(self):
        return len(self.cases)


# 自动化测试接口用例
class AutoTestCase(db.Model):
    __tablename__ = 'auto_test_cases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('auto_test_groups.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)  # 接口名称
    method = db.Column(db.String(10), nullable=False, default='GET')  # 请求方法
    url = db.Column(db.String(2000), nullable=False)  # 请求URL
    description = db.Column(db.Text)  # 接口描述
    headers = db.Column(db.Text)  # 请求头（JSON格式）
    extractors = db.Column(db.Text)  # 变量提取规则（JSON格式数组）
    assertions = db.Column(db.Text)  # 断言规则（JSON格式数组）
    # 断言规则格式: [{"target": "status_code", "operator": "==", "expected": "200", "expression": ""}, ...]
    body = db.Column(db.Text)  # 请求体
    body_type = db.Column(db.String(20), default='json')  # 请求体类型
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('auto_test_cases', lazy=True))
    group = db.relationship('AutoTestGroup', backref=db.backref('cases', lazy=True))


# 自动化测试计划（场景）
class AutoTestPlan(db.Model):
    __tablename__ = 'test_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # 计划名称
    description = db.Column(db.Text)  # 计划描述
    environment_id = db.Column(db.Integer, nullable=True)  # 默认测试环境（表 environments 已经存在于数据库）
    case_ids = db.Column(db.Text, nullable=False)  # 选中接口ID列表 JSON格式，保存排序（兼容旧格式）
    data_matrix = db.Column(db.Text, nullable=True)  # 数据驱动数据集 JSON格式
    cron_expression = db.Column(db.String(50), nullable=True)  # Cron 定时表达式
    webhook_url = db.Column(db.String(500), nullable=True)  # 钉钉/企微/飞书机器人 Webhook 告警地址
    webhook_token = db.Column(db.String(64), unique=True, default=lambda: str(uuid.uuid4()), comment="CI/CD触发Token")  # CI/CD 外部触发唯一Token
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('auto_test_plans', lazy=True))
    steps = db.relationship('AutoTestStep', backref='scenario', lazy=True, cascade='all, delete-orphan')


# 定时调度任务
class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scenario_id = db.Column(db.Integer, db.ForeignKey('test_scenarios.id'), nullable=False)
    name = db.Column(db.String(200), nullable=True)  # 任务名称
    cron_expression = db.Column(db.String(50), nullable=False)  # Cron 表达式
    env_id = db.Column(db.Integer, nullable=True)  # 执行环境（表 environments 已经存在于数据库）
    webhook_url = db.Column(db.String(500), nullable=True)  # Webhook 告警地址
    is_active = db.Column(db.Boolean, default=True)
    last_run_at = db.Column(db.DateTime, nullable=True)  # 上次执行时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('scheduled_tasks', lazy=True))
    scenario = db.relationship('AutoTestPlan', backref=db.backref('scheduled_tasks', lazy=True))


# 自动化测试场景步骤
class AutoTestStep(db.Model):
    __tablename__ = 'auto_test_steps'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('test_scenarios.id'), nullable=False)
    api_case_id = db.Column(db.Integer, db.ForeignKey('auto_test_cases.id'), nullable=False)
    step_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    variable_overrides = db.Column(db.Text, nullable=True)  # 局部变量覆盖 JSON
    extractors = db.Column(db.Text, nullable=True)  # 🔍 后置提取规则 JSON 数组
    # 格式: [{"variable_name": "token", "json_path": "$.data.token"}, ...]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    api_case = db.relationship('AutoTestCase', backref='steps', lazy=True)


# 自动化测试报告
class AutoTestReport(db.Model):
    __tablename__ = 'auto_test_reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('test_scenarios.id'), nullable=True)
    plan_name = db.Column(db.String(200))  # 计划名称快照
    total_count = db.Column(db.Integer, default=0)  # 总用例数
    success_count = db.Column(db.Integer, default=0)  # 成功数
    failed_count = db.Column(db.Integer, default=0)  # 失败数
    total_time = db.Column(db.Integer, default=0)  # 总耗时毫秒
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('auto_test_reports', lazy=True))
    plan = db.relationship('AutoTestPlan', backref=db.backref('reports', lazy=True))
    results = db.relationship('AutoTestReportResult', backref='report', lazy=True, cascade='all, delete-orphan')


# 自动化测试报告结果（单个用例执行结果
class AutoTestReportResult(db.Model):
    __tablename__ = 'auto_test_report_results'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('auto_test_reports.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('auto_test_cases.id'), nullable=True)
    case_name = db.Column(db.String(200))
    method = db.Column(db.String(10))
    url = db.Column(db.String(2000))
    status_code = db.Column(db.Integer)
    success = db.Column(db.Boolean, default=False)
    time_ms = db.Column(db.Integer, default=0)
    error = db.Column(db.Text)
    request_headers = db.Column(db.Text)
    request_body = db.Column(db.Text)
    response_body = db.Column(db.Text)
    response_headers = db.Column(db.Text)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    case = db.relationship('AutoTestCase', backref=db.backref('report_results', lazy=True))


# 高危操作审计日志
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    action = db.Column(db.String(200), nullable=False)  # 动作描述，如"全量数据库备份"、"恢复数据库备份"
    action_type = db.Column(db.String(50), nullable=False)  # 分类：backup/restore/delete/admin
    ip_address = db.Column(db.String(50))  # 操作IP地址
    status = db.Column(db.String(20), default='success')  # success/failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))