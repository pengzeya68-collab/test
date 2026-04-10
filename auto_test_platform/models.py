"""
数据库模型
按照用户的 Prompt 1 要求设计

模型:
- ApiGroup: 接口分组表（树状结构）
- ApiCase: 用例表
- Environment: 环境变量表
- TestHistory: 测试历史记录表
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from auto_test_platform.database import Base


class ApiGroup(Base):
    """
    接口分组表
    支持树状结构（通过 parent_id 实现父子分组）
    """
    __tablename__ = "api_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="分组名称")
    parent_id = Column(Integer, ForeignKey("api_groups.id"), nullable=True, comment="父级分组ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    parent = relationship("ApiGroup", remote_side=[id], backref="children")
    cases = relationship("ApiCase", back_populates="group", cascade="all, delete-orphan")


class ApiCase(Base):
    """
    用例表
    存储接口测试的用例信息
    """
    __tablename__ = "api_cases"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("api_groups.id"), nullable=False, comment="所属分组")
    name = Column(String(200), nullable=False, comment="用例名称")
    method = Column(String(10), nullable=False, default="GET", comment="请求方法")
    url = Column(Text, nullable=False, comment="接口地址（支持 {{variable}} 占位符）")
    headers = Column(JSON, nullable=True, comment="请求头（JSON格式）")
    payload = Column(JSON, nullable=True, comment="请求体（JSON格式）")
    assert_rules = Column(JSON, nullable=True, comment="断言规则（JSON格式）")
    description = Column(Text, nullable=True, comment="用例描述")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    group = relationship("ApiGroup", back_populates="cases")
    history = relationship("TestHistory", back_populates="case", cascade="all, delete-orphan")


class Environment(Base):
    """
    环境变量表
    存储不同测试环境的配置
    """
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    env_name = Column(String(100), nullable=False, comment="环境名称（如：测试环境）")
    base_url = Column(String(500), nullable=True, comment="基础路径")
    variables = Column(JSON, nullable=True, default=dict, comment="全局变量（JSON格式）")
    is_default = Column(Boolean, default=False, comment="是否为默认环境")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class TestHistory(Base):
    """
    测试历史记录表
    记录每次测试执行的结果
    """
    __tablename__ = "test_history"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("api_cases.id"), nullable=False, comment="用例ID")
    status = Column(String(20), nullable=False, comment="执行状态：success/failed/error")
    execution_time = Column(Integer, nullable=True, comment="执行耗时（毫秒）")
    report_url = Column(String(500), nullable=True, comment="Allure 报告相对路径")
    response_data = Column(JSON, nullable=True, comment="响应数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="执行时间")

    # 关联关系
    case = relationship("ApiCase", back_populates="history")


class TestScenario(Base):
    """
    测试场景表
    用于编排多个接口的执行顺序，实现流程测试
    """
    __tablename__ = "test_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="场景名称")
    description = Column(Text, nullable=True, comment="场景描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    steps = relationship("ScenarioStep", back_populates="scenario", cascade="all, delete-orphan", order_by="ScenarioStep.step_order")
    dataset = relationship("TestDataset", back_populates="scenario", uselist=False, cascade="all, delete-orphan")
    execution_records = relationship("ScenarioExecutionRecord", back_populates="scenario", cascade="all, delete-orphan")


class ScenarioStep(Base):
    """
    场景步骤表
    定义场景中每个步骤引用的接口和执行顺序
    """
    __tablename__ = "scenario_steps"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("test_scenarios.id"), nullable=False, comment="所属场景ID")
    api_case_id = Column(Integer, ForeignKey("api_cases.id"), nullable=False, comment="引用的接口ID")
    step_order = Column(Integer, nullable=False, default=0, comment="执行顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    # 局部变量覆盖：允许在这个场景中覆盖接口的某些参数
    # 格式：{"headers": {"token": "xxx"}, "payload": {"user_id": 123}, "url": "/new/path"}
    variable_overrides = Column(JSON, nullable=True, comment="局部变量覆盖")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    scenario = relationship("TestScenario", back_populates="steps")
    api_case = relationship("ApiCase")


class TestDataset(Base):
    """
    测试数据集表
    存储数据驱动的二维表格数据，类似 pytest.mark.parametrize
    """
    __tablename__ = "test_datasets"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("test_scenarios.id"), nullable=False, unique=True, comment="所属场景ID（一个场景只有一个数据集）")
    name = Column(String(200), nullable=False, default="默认数据集", comment="数据集名称")
    # data_matrix: 二维表格数据
    # {
    #   "columns": ["username", "password", "expected_status"],  // 变量名（第一行）
    #   "rows": [                                                   // 数据行
    #     ["user1", "pass1", 200],
    #     ["user2", "pass2", 401],
    #   ]
    # }
    data_matrix = Column(JSON, nullable=False, default={"columns": [], "rows": []}, comment="数据矩阵")
    description = Column(Text, nullable=True, comment="数据集描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    scenario = relationship("TestScenario", back_populates="dataset")


class ScenarioExecutionRecord(Base):
    """
    场景执行历史记录表
    记录每次场景执行的结果统计
    """
    __tablename__ = "scenario_execution_records"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("test_scenarios.id"), nullable=False, comment="场景ID")
    status = Column(String(20), nullable=False, comment="执行状态: success/failed/error")
    total_steps = Column(Integer, nullable=False, default=0, comment="总步骤数")
    failed_steps = Column(Integer, nullable=False, default=0, comment="失败步骤数")
    success_steps = Column(Integer, nullable=False, default=0, comment="成功步骤数")
    skipped_steps = Column(Integer, nullable=False, default=0, comment="跳过步骤数")
    total_time = Column(Integer, nullable=True, comment="执行总耗时（毫秒）")
    report_url = Column(String(500), nullable=True, comment="Allure 报告相对路径")
    created_at = Column(DateTime, default=datetime.utcnow, comment="执行时间")

    # 关联关系
    scenario = relationship("TestScenario", back_populates="execution_records")
