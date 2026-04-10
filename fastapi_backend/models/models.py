"""
数据模型 - 与实际数据库表名和列名匹配
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from fastapi_backend.core.database import Base


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
