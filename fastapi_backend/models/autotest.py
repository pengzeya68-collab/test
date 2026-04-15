"""
AutoTest 模型 - 使用 auto_test_platform 原始表名确保数据兼容

这些模型映射到 auto_test_platform 的原有 SQLite 表，
与 fastapi_backend/models/models.py 中的同名类（不同表名）不冲突。
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from fastapi_backend.core.autotest_database import AutoTestBase as Base


class AutoTestGroup(Base):
    """接口分组表（auto_test_platform 原始表）"""
    __tablename__ = "api_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="分组名称")
    parent_id = Column(Integer, ForeignKey("api_groups.id"), nullable=True, comment="父级分组ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    parent = relationship("AutoTestGroup", remote_side=[id], backref="children")
    cases = relationship("AutoTestCase", back_populates="group", cascade="all, delete-orphan")


class AutoTestCase(Base):
    """接口用例表（auto_test_platform 原始表）"""
    __tablename__ = "api_cases"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("api_groups.id"), nullable=False, comment="所属分组")
    name = Column(String(200), nullable=False, comment="用例名称")
    method = Column(String(10), nullable=False, default="GET", comment="请求方法")
    url = Column(Text, nullable=False, comment="接口地址")
    headers = Column(JSON, nullable=True, comment="请求头")
    # 使用 nullable=True 确保即使表中不存在该列，模型也能正常工作
    params = Column(JSON, nullable=True, comment="请求参数")
    body_type = Column(String(20), nullable=True, default="none", comment="body类型: none/raw/form-data")
    content_type = Column(String(50), nullable=True, default="application/json", comment="Content-Type")
    payload = Column(JSON, nullable=True, comment="请求体")
    assert_rules = Column(JSON, nullable=True, comment="断言规则")
    extractors = Column(JSON, nullable=True, comment="变量提取规则")
    description = Column(Text, nullable=True, comment="用例描述")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
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
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class AutoTestEnvironment(Base):
    """测试环境表（auto_test_platform 原始表）"""
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    env_name = Column(String(100), nullable=False, comment="环境名称")
    base_url = Column(String(500), nullable=True, comment="基础路径")
    variables = Column(JSON, nullable=True, default=dict, comment="环境变量")
    is_default = Column(Boolean, default=False, comment="是否默认环境")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class AutoTestHistory(Base):
    """测试历史记录表（auto_test_platform 原始表）"""
    __tablename__ = "test_history"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("api_cases.id"), nullable=False, comment="用例ID")
    status = Column(String(20), nullable=False, comment="执行状态")
    execution_time = Column(Integer, nullable=True, comment="执行耗时(ms)")
    report_url = Column(String(500), nullable=True, comment="报告路径")
    response_data = Column(JSON, nullable=True, comment="响应数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="执行时间")

    # 关联关系
    case = relationship("AutoTestCase", back_populates="history")


class AutoTestScenario(Base):
    """测试场景表（auto_test_platform 原始表）"""
    __tablename__ = "test_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="场景名称")
    description = Column(Text, nullable=True, comment="场景描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    # 定时任务配置（持久化，避免仅内存导致重载后丢失）
    schedule_cron_expression = Column(String(200), nullable=True, comment="Cron 表达式")
    schedule_env_id = Column(Integer, nullable=True, comment="定时执行环境 ID")
    schedule_webhook_url = Column(Text, nullable=True, comment="定时任务 Webhook 告警地址")
    schedule_task_name = Column(String(200), nullable=True, comment="定时任务显示名称")
    schedule_is_active = Column(Boolean, default=True, comment="定时任务是否启用（未暂停）")

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

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("test_scenarios.id"), nullable=False, comment="所属场景ID")
    api_case_id = Column(Integer, ForeignKey("api_cases.id"), nullable=False, comment="引用的接口ID")
    step_order = Column(Integer, nullable=False, default=0, comment="执行顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    variable_overrides = Column(JSON, nullable=True, comment="局部变量覆盖")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    scenario = relationship("AutoTestScenario", back_populates="steps")
    api_case = relationship("AutoTestCase")


class AutoTestDataset(Base):
    """测试数据集表（auto_test_platform 原始表）"""
    __tablename__ = "test_datasets"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("test_scenarios.id"),
        nullable=False,
        unique=True,
        comment="所属场景ID",
    )
    name = Column(String(200), nullable=False, default="默认数据集", comment="数据集名称")
    data_matrix = Column(JSON, nullable=False, default={"columns": [], "rows": []}, comment="数据矩阵")
    description = Column(Text, nullable=True, comment="数据集描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    scenario = relationship("AutoTestScenario", back_populates="dataset")


class AutoTestScenarioExecutionRecord(Base):
    """场景执行历史记录表（auto_test_platform 原始表）"""
    __tablename__ = "scenario_execution_records"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("test_scenarios.id"), nullable=False, comment="场景ID")
    status = Column(String(20), nullable=False, comment="执行状态")
    total_steps = Column(Integer, nullable=False, default=0, comment="总步骤数")
    failed_steps = Column(Integer, nullable=False, default=0, comment="失败步骤数")
    success_steps = Column(Integer, nullable=False, default=0, comment="成功步骤数")
    skipped_steps = Column(Integer, nullable=False, default=0, comment="跳过步骤数")
    total_time = Column(Integer, nullable=True, comment="执行总耗时(ms)")
    report_url = Column(String(500), nullable=True, comment="报告路径")
    created_at = Column(DateTime, default=datetime.utcnow, comment="执行时间")

    scenario = relationship("AutoTestScenario", back_populates="execution_records")
