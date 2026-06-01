"""
AutoTest 模型 - 使用 auto_test_platform 原始表名确保数据兼容

这些模型映射到 auto_test_platform 的原有表，
现已合并到主 PostgreSQL 数据库，使用统一的 Base。
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from fastapi_backend.core.database import Base


class AutoTestGroup(Base):
    """接口分组表（auto_test_platform 原始表）"""

    __tablename__ = "api_groups"
    __table_args__ = (Index("idx_api_groups_parent_id", "parent_id"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="分组名称")
    parent_id = Column(
        Integer,
        ForeignKey("api_groups.id", ondelete="SET NULL"),
        nullable=True,
        comment="父级分组ID",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    parent = relationship("AutoTestGroup", remote_side=[id], backref="children")
    cases = relationship("AutoTestCase", back_populates="group", cascade="all, delete-orphan")


class AutoTestCase(Base):
    """接口用例表（auto_test_platform 原始表）"""

    __tablename__ = "api_cases"
    __table_args__ = (Index("idx_api_cases_group_id", "group_id"),)

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(
        Integer,
        ForeignKey("api_groups.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属分组",
    )
    name = Column(String(200), nullable=False, comment="用例名称")
    method = Column(String(10), nullable=False, default="GET", comment="请求方法")
    url = Column(Text, nullable=False, comment="接口地址")
    headers = Column(JSON, nullable=True, comment="请求头")
    params = Column(JSON, nullable=True, comment="请求参数")
    body_type = Column(
        String(20),
        nullable=True,
        default="none",
        comment="body类型: none/raw/form-data",
    )
    content_type = Column(String(50), nullable=True, default="application/json", comment="Content-Type")
    payload = Column(JSON, nullable=True, comment="请求体")
    assert_rules = Column(JSON, nullable=True, comment="断言规则")
    extractors = Column(JSON, nullable=True, comment="变量提取规则")
    description = Column(Text, nullable=True, comment="用例描述")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    group = relationship("AutoTestGroup", back_populates="cases")
    history = relationship("AutoTestHistory", back_populates="case", cascade="all, delete-orphan")


class AutoTestGlobalVariable(Base):
    """全局变量表"""

    __tablename__ = "global_variables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="变量名")
    value = Column(Text, nullable=False, comment="变量值")
    description = Column(Text, nullable=True, comment="变量描述")
    is_encrypted = Column(Boolean, default=False, comment="是否加密")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )


class AutoTestEnvironment(Base):
    """测试环境表（auto_test_platform 原始表）"""

    __tablename__ = "environments"
    __table_args__ = (Index("idx_environments_is_default", "is_default"),)

    id = Column(Integer, primary_key=True, index=True)
    env_name = Column(String(100), nullable=False, unique=True, comment="环境名称")
    base_url = Column(String(500), nullable=True, comment="基础路径")
    variables = Column(JSON, nullable=True, default=dict, comment="环境变量")
    is_default = Column(Boolean, default=False, comment="是否默认环境")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )


class AutoTestHistory(Base):
    """测试历史记录表（auto_test_platform 原始表）"""

    __tablename__ = "test_history"
    __table_args__ = (
        Index("idx_test_history_case_id", "case_id"),
        Index("idx_test_history_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(
        Integer,
        ForeignKey("api_cases.id", ondelete="CASCADE"),
        nullable=False,
        comment="用例ID",
    )
    status = Column(String(20), nullable=False, comment="执行状态")
    execution_time = Column(Integer, nullable=True, comment="执行耗时(ms)")
    report_url = Column(String(500), nullable=True, comment="报告路径")
    response_data = Column(JSON, nullable=True, comment="响应数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="执行时间",
    )

    case = relationship("AutoTestCase", back_populates="history")


class AutoTestScenario(Base):
    """测试场景表（auto_test_platform 原始表）"""

    __tablename__ = "test_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="场景名称")
    description = Column(Text, nullable=True, comment="场景描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )
    schedule_cron_expression = Column(String(200), nullable=True, comment="Cron 表达式")
    schedule_env_id = Column(Integer, nullable=True, comment="定时执行环境 ID")
    schedule_webhook_url = Column(Text, nullable=True, comment="定时任务 Webhook 告警地址")
    schedule_task_name = Column(String(200), nullable=True, comment="定时任务显示名称")
    schedule_is_active = Column(Boolean, default=True, comment="定时任务是否启用（未暂停）")
    project_id = Column(Integer, nullable=True, comment="关联的项目实战ID（NULL表示不限项目）")
    webhook_token = Column(
        String(64),
        nullable=True,
        comment="CI/CD Webhook 触发令牌",
        index=True,
        unique=True,
    )
    fail_fast = Column(Boolean, default=False, comment="步骤失败时是否立即停止后续步骤")

    steps = relationship(
        "AutoTestScenarioStep",
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="AutoTestScenarioStep.step_order",
    )
    dataset = relationship(
        "AutoTestDataset",
        back_populates="scenario",
        uselist=False,
        cascade="all, delete-orphan",
    )
    execution_records = relationship(
        "AutoTestScenarioExecutionRecord",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )


class AutoTestScenarioStep(Base):
    """场景步骤表（auto_test_platform 原始表）"""

    __tablename__ = "scenario_steps"
    __table_args__ = (
        Index("idx_scenario_steps_scenario_id", "scenario_id"),
        Index("idx_scenario_steps_api_case_id", "api_case_id"),
        UniqueConstraint("scenario_id", "step_order", name="uq_scenario_step_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("test_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属场景ID",
    )
    api_case_id = Column(
        Integer,
        ForeignKey("api_cases.id", ondelete="SET NULL"),
        nullable=True,
        comment="引用的接口ID",
    )
    step_order = Column(Integer, nullable=False, default=0, comment="执行顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    variable_overrides = Column(JSON, nullable=True, comment="局部变量覆盖")
    condition = Column(JSON, nullable=True, comment="条件执行规则: {field, operator, value}")
    on_error = Column(String(20), nullable=False, default="stop", comment="错误处理: stop/continue/retry")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")
    retry_delay_ms = Column(Integer, nullable=False, default=1000, comment="重试间隔(ms)")
    wait_ms = Column(Integer, nullable=False, default=0, comment="执行前等待(ms)")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    scenario = relationship("AutoTestScenario", back_populates="steps")
    api_case = relationship("AutoTestCase")


class AutoTestDataset(Base):
    """测试数据集表（auto_test_platform 原始表）"""

    __tablename__ = "test_datasets"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("test_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="所属场景ID",
    )
    name = Column(String(200), nullable=False, default="默认数据集", comment="数据集名称")
    data_matrix = Column(
        JSON,
        nullable=False,
        default=lambda: {"columns": [], "rows": []},
        comment="数据矩阵",
    )
    description = Column(Text, nullable=True, comment="数据集描述")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    scenario = relationship("AutoTestScenario", back_populates="dataset")


class AutoTestScenarioExecutionRecord(Base):
    """场景执行历史记录表（auto_test_platform 原始表）"""

    __tablename__ = "scenario_execution_records"
    __table_args__ = (
        Index("idx_scenario_exec_records_scenario_id", "scenario_id"),
        Index("idx_scenario_exec_records_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("test_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        comment="场景ID",
    )
    env_id = Column(Integer, nullable=True, comment="执行环境ID")
    status = Column(String(20), nullable=False, comment="执行状态")
    total_steps = Column(Integer, nullable=False, default=0, comment="总步骤数")
    failed_steps = Column(Integer, nullable=False, default=0, comment="失败步骤数")
    success_steps = Column(Integer, nullable=False, default=0, comment="成功步骤数")
    skipped_steps = Column(Integer, nullable=False, default=0, comment="跳过步骤数")
    total_time = Column(Integer, nullable=True, comment="执行总耗时(ms)")
    report_url = Column(String(500), nullable=True, comment="报告路径")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="执行时间",
    )

    scenario = relationship("AutoTestScenario", back_populates="execution_records")


# ========== 性能测试模型 ==========


class AutoTestPerformanceScenario(Base):
    """性能测试场景表"""

    __tablename__ = "performance_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="场景名称")
    description = Column(Text, nullable=True, comment="场景描述")
    test_type = Column(String(20), nullable=False, default="load", comment="测试类型: load/stress/soak")
    config = Column(JSON, nullable=True, default=dict, comment="测试配置")
    status = Column(String(20), nullable=False, default="inactive", comment="状态: active/inactive")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    steps = relationship(
        "AutoTestPerformanceScenarioStep",
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="AutoTestPerformanceScenarioStep.step_order",
    )
    executions = relationship(
        "AutoTestPerformanceExecutionRecord",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )


class AutoTestPerformanceScenarioStep(Base):
    """性能测试场景步骤表（引用接口用例）"""

    __tablename__ = "performance_scenario_steps"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("performance_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属场景ID",
    )
    api_case_id = Column(Integer, ForeignKey("api_cases.id"), nullable=False, comment="引用的接口ID")
    step_order = Column(Integer, nullable=False, default=0, comment="执行顺序")
    weight = Column(Integer, nullable=False, default=1, comment="权重（用于混合场景）")
    think_time = Column(Integer, nullable=False, default=0, comment="思考时间(ms)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    scenario = relationship("AutoTestPerformanceScenario", back_populates="steps")
    api_case = relationship("AutoTestCase")


class AutoTestPerformanceExecutionRecord(Base):
    """性能测试执行记录表"""

    __tablename__ = "performance_execution_records"
    __table_args__ = (Index("idx_perf_exec_records_scenario_id", "scenario_id"),)

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("performance_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        comment="场景ID",
    )
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="执行状态: pending/running/completed/failed",
    )
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="结束时间")

    total_requests = Column(Integer, nullable=True, comment="总请求数")
    failed_requests = Column(Integer, nullable=True, comment="失败请求数")
    avg_response_time = Column(Integer, nullable=True, comment="平均响应时间(ms)")
    min_response_time = Column(Integer, nullable=True, comment="最小响应时间(ms)")
    max_response_time = Column(Integer, nullable=True, comment="最大响应时间(ms)")
    p50_response_time = Column(Integer, nullable=True, comment="P50响应时间(ms)")
    p95_response_time = Column(Integer, nullable=True, comment="P95响应时间(ms)")
    p99_response_time = Column(Integer, nullable=True, comment="P99响应时间(ms)")
    requests_per_second = Column(Integer, nullable=True, comment="每秒请求数(RPS)")
    error_rate = Column(Float, nullable=True, comment="错误率(%)")

    report_url = Column(String(500), nullable=True, comment="报告路径")
    report_data = Column(JSON, nullable=True, comment="报告数据（JSON格式）")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    scenario = relationship("AutoTestPerformanceScenario", back_populates="executions")
    metrics = relationship(
        "AutoTestPerformanceMetrics",
        back_populates="execution",
        cascade="all, delete-orphan",
    )


class AutoTestPerformanceMetrics(Base):
    """性能指标时序数据表"""

    __tablename__ = "performance_metrics"
    __table_args__ = (Index("idx_perf_metrics_execution_id", "execution_id"),)

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(
        Integer,
        ForeignKey("performance_execution_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="执行记录ID",
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, comment="时间戳")

    active_users = Column(Integer, nullable=True, comment="活跃用户数")
    current_rps = Column(Integer, nullable=True, comment="当前RPS")
    avg_response_time = Column(Integer, nullable=True, comment="平均响应时间(ms)")
    min_response_time = Column(Integer, nullable=True, comment="最小响应时间(ms)")
    max_response_time = Column(Integer, nullable=True, comment="最大响应时间(ms)")
    p95_response_time = Column(Integer, nullable=True, comment="P95响应时间(ms)")
    failed_requests = Column(Integer, nullable=True, comment="失败请求数")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    execution = relationship("AutoTestPerformanceExecutionRecord", back_populates="metrics")


# ========== 测试数据工厂模型 ==========


class TestDataTemplate(Base):
    """测试数据模板表"""

    __tablename__ = "test_data_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    user_id = Column(Integer, nullable=True, index=True, comment="创建者用户ID(跨库引用，非FK)")
    scenario_id = Column(
        Integer,
        ForeignKey("test_scenarios.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联场景ID",
    )
    row_count = Column(Integer, default=10, comment="生成行数")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    fields = relationship(
        "TestDataTemplateField",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TestDataTemplateField.sort_order",
    )


class TestDataTemplateField(Base):
    """测试数据模板字段规则表"""

    __tablename__ = "test_data_template_fields"
    __table_args__ = (Index("idx_template_fields_template_id", "template_id"),)

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(
        Integer,
        ForeignKey("test_data_templates.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属模板ID",
    )
    field_name = Column(String(100), nullable=False, comment="字段名")
    field_label = Column(String(200), nullable=True, comment="字段标签")
    rule_type = Column(
        String(50),
        nullable=False,
        comment="规则类型: fixed/enum/increment/uuid/timestamp/date_offset/phone/email/username/env_ref",
    )
    rule_config = Column(JSON, nullable=True, comment="规则配置JSON")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    template = relationship("TestDataTemplate", back_populates="fields")


# ========== Mock 服务模型 ==========


class MockProject(Base):
    """Mock 项目表"""

    __tablename__ = "mock_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    base_url_slug = Column(String(100), nullable=False, unique=True, comment="URL标识(slug)")
    swagger_source_id = Column(Integer, nullable=True, comment="关联的Swagger数据源ID")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    rules = relationship("MockRule", back_populates="project", cascade="all, delete-orphan")
    request_logs = relationship("MockRequestLog", back_populates="project", cascade="all, delete-orphan")


class MockRule(Base):
    """Mock 规则表"""

    __tablename__ = "mock_rules"
    __table_args__ = (Index("idx_mock_rules_project_id", "project_id"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("mock_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属项目ID",
    )
    method = Column(String(10), nullable=False, default="GET", comment="请求方法")
    path = Column(String(500), nullable=False, comment="匹配路径(支持通配符)")
    name = Column(String(200), nullable=True, comment="规则名称")
    description = Column(Text, nullable=True, comment="规则描述")
    response_status = Column(Integer, nullable=False, default=200, comment="响应状态码")
    response_headers = Column(JSON, nullable=True, default=dict, comment="响应头")
    response_body = Column(JSON, nullable=True, comment="响应体(JSON)")
    delay_ms = Column(Integer, nullable=False, default=0, comment="模拟延迟(毫秒)")
    condition = Column(JSON, nullable=True, comment="条件响应规则")
    priority = Column(Integer, nullable=False, default=0, comment="优先级(越高越优先)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    project = relationship("MockProject", back_populates="rules")


class MockRequestLog(Base):
    """Mock 请求日志表"""

    __tablename__ = "mock_request_logs"
    __table_args__ = (
        Index("idx_mock_logs_project_id", "project_id"),
        Index("idx_mock_logs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("mock_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属项目ID",
    )
    rule_id = Column(Integer, nullable=True, comment="匹配到的规则ID")
    method = Column(String(10), nullable=False, comment="请求方法")
    path = Column(String(500), nullable=False, comment="请求路径")
    request_headers = Column(JSON, nullable=True, comment="请求头")
    request_body = Column(Text, nullable=True, comment="请求体")
    response_status = Column(Integer, nullable=True, comment="响应状态码")
    response_body = Column(Text, nullable=True, comment="响应体")
    response_time_ms = Column(Integer, nullable=True, comment="响应耗时(ms)")
    matched_rule_name = Column(String(200), nullable=True, comment="匹配的规则名称")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="请求时间",
    )

    project = relationship("MockProject", back_populates="request_logs")


# ========== 测试套件模型 ==========


class TestSuite(Base):
    """测试套件表"""

    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="套件名称")
    description = Column(Text, nullable=True, comment="套件描述")
    env_id = Column(Integer, nullable=True, comment="默认执行环境ID")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    cases = relationship("TestSuiteCase", back_populates="suite", cascade="all, delete-orphan")
    executions = relationship("TestSuiteExecution", back_populates="suite", cascade="all, delete-orphan")


class TestSuiteCase(Base):
    """套件-用例关联表"""

    __tablename__ = "test_suite_cases"
    __table_args__ = (
        Index("idx_suite_cases_suite_id", "suite_id"),
        UniqueConstraint("suite_id", "case_id", name="uq_suite_case"),
    )

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(
        Integer,
        ForeignKey("test_suites.id", ondelete="CASCADE"),
        nullable=False,
        comment="套件ID",
    )
    case_id = Column(
        Integer,
        ForeignKey("api_cases.id", ondelete="CASCADE"),
        nullable=False,
        comment="用例ID",
    )
    sort_order = Column(Integer, nullable=False, default=0, comment="执行顺序")

    suite = relationship("TestSuite", back_populates="cases")
    case = relationship("AutoTestCase")


class TestSuiteExecution(Base):
    """套件执行记录表"""

    __tablename__ = "test_suite_executions"
    __table_args__ = (Index("idx_suite_exec_suite_id", "suite_id"),)

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(
        Integer,
        ForeignKey("test_suites.id", ondelete="CASCADE"),
        nullable=False,
        comment="套件ID",
    )
    env_id = Column(Integer, nullable=True, comment="执行环境ID")
    status = Column(String(20), nullable=False, default="pending", comment="执行状态")
    total_cases = Column(Integer, nullable=False, default=0, comment="总用例数")
    passed_cases = Column(Integer, nullable=False, default=0, comment="通过用例数")
    failed_cases = Column(Integer, nullable=False, default=0, comment="失败用例数")
    duration_ms = Column(Integer, nullable=True, comment="执行总耗时(ms)")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    finished_at = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    suite = relationship("TestSuite", back_populates="executions")
