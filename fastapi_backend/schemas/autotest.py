"""
AutoTest Pydantic Schema 模型
用于请求校验和响应序列化
"""
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime


# 可空整数类型：自动将空字符串转换为 None
def empty_str_to_none(v):
    if v == "":
        return None
    return v

OptionalInt = Annotated[Optional[int], BeforeValidator(empty_str_to_none)]


# ========== AutoTestGroup Schema ==========

class AutoTestGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="分组名称")
    parent_id: Optional[Any] = Field(None, description="父级分组ID")


class AutoTestGroupCreate(AutoTestGroupBase):
    pass


class AutoTestGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: OptionalInt = None


class AutoTestGroupResponse(AutoTestGroupBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutoTestGroupTree(AutoTestGroupResponse):
    children: List["AutoTestGroupTree"] = []
    case_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ========== AutoTestCase Schema ==========

class AutoTestCaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="用例名称")
    method: str = Field(default="GET", description="请求方法")
    url: str = Field(..., description="接口地址")
    headers: Optional[Dict[str, Any]] = Field(None, description="请求头")
    params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    body_type: Optional[str] = Field(None, description="body类型: none/raw/form-data")
    content_type: Optional[str] = Field(None, description="Content-Type")
    payload: Optional[Dict[str, Any]] = Field(None, description="请求体")
    assert_rules: Optional[Any] = Field(None, alias="assertions", description="断言规则")
    extractors: Optional[List[Dict[str, Any]]] = Field(None, description="变量提取规则")
    description: Optional[str] = Field(None, description="用例描述")

    model_config = ConfigDict(populate_by_name=True)


class AutoTestCaseCreate(AutoTestCaseBase):
    group_id: Any = Field(..., description="所属分组ID")


class AutoTestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    body_type: Optional[str] = None
    content_type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    assert_rules: Optional[Any] = Field(None, alias="assertions", description="断言规则")
    extractors: Optional[List[Dict[str, Any]]] = Field(None, description="变量提取规则")
    description: Optional[str] = None
    group_id: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class AutoTestCaseResponse(AutoTestCaseBase):
    id: int
    group_id: Any
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== AutoTestEnvironment Schema ==========

class AutoTestEnvironmentBase(BaseModel):
    env_name: str = Field(..., min_length=1, max_length=100, description="环境名称")
    base_url: Optional[str] = Field(None, description="基础路径")
    variables: Dict[str, Any] = Field(default_factory=dict, description="全局变量")
    is_default: bool = Field(False, description="是否为默认环境")


class AutoTestEnvironmentCreate(AutoTestEnvironmentBase):
    pass


class AutoTestEnvironmentUpdate(BaseModel):
    env_name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class AutoTestEnvironmentResponse(AutoTestEnvironmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== AutoTestHistory Schema ==========

class AutoTestHistoryResponse(BaseModel):
    id: int
    case_id: Any
    status: str
    execution_time: Optional[int] = None
    report_url: Optional[str] = None
    response_data: Optional[Any] = Field(None, description="接口实际响应内容，可能为dict, list或str")
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 执行结果 Schema ==========

class CaseRunRequest(BaseModel):
    env_id: Optional[Any] = Field(None, description="环境ID")

class CaseExecutionResult(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response: Optional[Any] = None
    execution_time: int = 0
    error: Optional[str] = None
    assert_result: Optional[Dict[str, Any]] = None
    request_body: Optional[Any] = None
    # 🔥 修复：返回已替换变量的请求数据，供前端显示真实发送内容
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    request_headers: Optional[Dict[str, Any]] = None
    request_params: Optional[Dict[str, Any]] = None


# ========== 场景 Schema ==========

class ScenarioStepBase(BaseModel):
    api_case_id: Any = Field(..., description="引用的接口ID")
    step_order: int = Field(default=0, description="执行顺序")
    is_active: bool = Field(True, description="是否启用")
    variable_overrides: Optional[Dict[str, Any]] = Field(None, description="局部变量覆盖")


class ScenarioStepCreate(ScenarioStepBase):
    scenario_id: Optional[Any] = Field(None, description="所属场景ID")


class ScenarioStepUpdate(BaseModel):
    api_case_id: Optional[Any] = None
    step_order: Optional[int] = None
    is_active: Optional[bool] = None
    variable_overrides: Optional[Dict[str, Any]] = None


class ScenarioStepResponse(ScenarioStepBase):
    id: int
    scenario_id: Any
    created_at: datetime
    api_case: Optional[AutoTestCaseResponse] = None

    model_config = ConfigDict(from_attributes=True)


class AutoTestScenarioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    is_active: bool = Field(True, description="是否启用")


class AutoTestScenarioCreate(AutoTestScenarioBase):
    pass


class AutoTestScenarioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AutoTestScenarioResponse(AutoTestScenarioBase):
    id: int
    created_at: datetime
    updated_at: datetime
    steps: List[ScenarioStepResponse] = []

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    model_config = ConfigDict(from_attributes=True)


class ScenarioExecutionResult(BaseModel):
    scenario_id: int
    scenario_name: str
    total_steps: int
    success_steps: int
    failed_steps: int
    duration: int
    context_vars: Dict[str, Any] = {}
    step_results: List[Dict[str, Any]] = []


# ========== 数据集 Schema ==========

class DataMatrix(BaseModel):
    columns: List[str] = Field(default_factory=list, description="变量名列表")
    rows: List[List[Any]] = Field(default_factory=list, description="数据行")


class AutoTestDatasetBase(BaseModel):
    name: str = Field(default="默认数据集", description="数据集名称")
    data_matrix: DataMatrix = Field(default_factory=DataMatrix, description="数据矩阵")
    description: Optional[str] = Field(None, description="数据集描述")


class AutoTestDatasetCreate(AutoTestDatasetBase):
    scenario_id: Any = Field(..., description="所属场景ID")


class AutoTestDatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, description="数据集名称")
    data_matrix: Optional[DataMatrix] = Field(None, description="数据矩阵")
    description: Optional[str] = None


class AutoTestDatasetResponse(AutoTestDatasetBase):
    id: int
    scenario_id: Any
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataDrivenExecutionResult(BaseModel):
    scenario_id: int
    scenario_name: str
    dataset_name: str
    total_iterations: int
    success_iterations: int
    failed_iterations: int
    total_duration: int
    iterations: List[Dict[str, Any]] = []


# ========== 调度任务 Schema ==========

class ScheduleTaskCreate(BaseModel):
    scenario_id: Any
    cron_expression: str
    env_id: Optional[Any] = None
    webhook_url: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = True


class ScheduleTaskResponse(BaseModel):
    task_id: str
    job_id: str
    scenario_id: Any
    env_id: Optional[Any]
    cron_expression: str
    webhook_url: Optional[str] = None
    name: str
    created_at: str
    last_run: Optional[str] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    report_url: Optional[str] = None
    status: str
    is_active: bool = True
    next_run_time: Optional[str] = None


# ========== 邮件配置 Schema ==========

class EmailConfig(BaseModel):
    enabled: bool
    smtpHost: str
    smtpPort: int
    smtpUser: str
    smtpPassword: str
    fromEmail: str
    adminToEmail: str
    enableSSL: bool
    baseUrl: str
    testToEmail: Optional[str] = ""


class TestEmailRequest(BaseModel):
    to_email: str


# ========== 变量预览 Schema ==========

class VariablePreviewRequest(BaseModel):
    text: str
    variables: Dict[str, Any] = Field(default_factory=dict)


class VariablePreviewResponse(BaseModel):
    original: str
    result: str
    found_variables: List[str]


# ========== 内联场景执行请求 Schema ==========

class InlineScenarioExecutionRequest(BaseModel):
    steps: List[dict] = Field(..., description="步骤列表")
    data_matrix: DataMatrix = Field(..., description="数据矩阵")
    env_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, description="环境变量")


# 重建前向引用
AutoTestGroupTree.model_rebuild()
