"""
Pydantic Schema 模型
用于请求校验和响应序列化
"""
from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime

# 自定义验证器：将空字符串转换为 None
# 解决前端下拉框清空后传递空字符串导致的 int 转换错误
def empty_str_to_none(v):
    if v == "":
        return None
    return v

# 可空整数类型：自动将空字符串转换为 None
OptionalInt = Annotated[Optional[int], BeforeValidator(empty_str_to_none)]


# ========== ApiGroup Schema ==========

class ApiGroupBase(BaseModel):
    """分组基础 Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="分组名称")
    parent_id: OptionalInt = Field(None, description="父级分组ID")


class ApiGroupCreate(ApiGroupBase):
    """创建分组"""
    pass


class ApiGroupUpdate(BaseModel):
    """更新分组"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: OptionalInt = None


class ApiGroupResponse(ApiGroupBase):
    """分组响应"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApiGroupTree(ApiGroupResponse):
    """树状分组（包含子分组）"""
    children: List["ApiGroupTree"] = []
    case_count: int = 0

    class Config:
        from_attributes = True


# ========== ApiCase Schema ==========

class ApiCaseBase(BaseModel):
    """用例基础 Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="用例名称")
    method: str = Field(default="GET", description="请求方法")
    url: str = Field(..., description="接口地址")
    headers: Optional[Dict[str, Any]] = Field(None, description="请求头")
    payload: Optional[Dict[str, Any]] = Field(None, description="请求体")
    assert_rules: Optional[Any] = Field(None, description="断言规则")
    description: Optional[str] = Field(None, description="用例描述")


class ApiCaseCreate(ApiCaseBase):
    """创建用例"""
    group_id: int = Field(..., description="所属分组ID")


class ApiCaseUpdate(BaseModel):
    """更新用例"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    assert_rules: Optional[Any] = None  # 接受 dict 或 list 格式
    description: Optional[str] = None
    group_id: Optional[int] = None


class ApiCaseResponse(ApiCaseBase):
    """用例响应"""
    id: int
    group_id: int
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Environment Schema ==========

class EnvironmentBase(BaseModel):
    """环境基础 Schema"""
    env_name: str = Field(..., min_length=1, max_length=100, description="环境名称")
    base_url: Optional[str] = Field(None, description="基础路径")
    variables: Dict[str, Any] = Field(default_factory=dict, description="全局变量")
    is_default: bool = Field(False, description="是否为默认环境")


class EnvironmentCreate(EnvironmentBase):
    """创建环境"""
    pass


class EnvironmentUpdate(BaseModel):
    """更新环境"""
    env_name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class EnvironmentResponse(EnvironmentBase):
    """环境响应"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ========== TestHistory Schema ==========

class TestHistoryResponse(BaseModel):
    """测试历史响应"""
    id: int
    case_id: int
    status: str
    execution_time: Optional[int] = None
    report_url: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 执行结果 Schema ==========

class CaseExecutionResult(BaseModel):
    """单个用例执行结果"""
    success: bool
    status_code: Optional[int] = None
    response: Optional[Any] = None  # 可以是 dict 或 list
    execution_time: int = 0
    error: Optional[str] = None
    assert_result: Optional[Dict[str, Any]] = None


class BatchExecutionResult(BaseModel):
    """批量执行结果"""
    total: int
    success: int
    failed: int
    results: List[CaseExecutionResult]


# ========== 变量替换预览 Schema ==========

class VariablePreviewRequest(BaseModel):
    """变量替换预览请求"""
    text: str
    variables: Dict[str, Any] = Field(default_factory=dict)


class VariablePreviewResponse(BaseModel):
    """变量替换预览响应"""
    original: str
    result: str
    found_variables: List[str]


# ========== TestScenario Schema ==========

class ScenarioStepBase(BaseModel):
    """步骤基础 Schema"""
    api_case_id: int = Field(..., description="引用的接口ID")
    step_order: int = Field(default=0, description="执行顺序")
    is_active: bool = Field(True, description="是否启用")
    variable_overrides: Optional[Dict[str, Any]] = Field(None, description="局部变量覆盖")


class ScenarioStepCreate(ScenarioStepBase):
    """创建步骤"""
    scenario_id: OptionalInt = Field(None, description="所属场景ID")


class ScenarioStepUpdate(BaseModel):
    """更新步骤"""
    api_case_id: OptionalInt = None
    step_order: Optional[int] = None
    is_active: Optional[bool] = None
    variable_overrides: Optional[Dict[str, Any]] = None


class ScenarioStepResponse(ScenarioStepBase):
    """步骤响应"""
    id: int
    scenario_id: int
    created_at: datetime

    # 包含接口详情
    api_case: Optional[ApiCaseResponse] = None

    class Config:
        from_attributes = True


class TestScenarioBase(BaseModel):
    """场景基础 Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    is_active: bool = Field(True, description="是否启用")


class TestScenarioCreate(TestScenarioBase):
    """创建场景"""
    pass


class TestScenarioUpdate(BaseModel):
    """更新场景"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TestScenarioResponse(TestScenarioBase):
    """场景响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    # 包含步骤列表
    steps: List[ScenarioStepResponse] = []

    class Config:
        from_attributes = True


class ScenarioExecutionResult(BaseModel):
    """场景执行结果"""
    scenario_id: int
    scenario_name: str
    total_steps: int
    success_steps: int
    failed_steps: int
    duration: int  # 总耗时 ms
    context_vars: Dict[str, Any] = {}  # 执行后的全局变量
    step_results: List[Dict[str, Any]] = []  # 每一步的结果


# ========== TestDataset Schema ==========

class DataMatrix(BaseModel):
    """数据矩阵结构"""
    columns: List[str] = Field(default_factory=list, description="变量名列表（第一行）")
    rows: List[List[Any]] = Field(default_factory=list, description="数据行（二维数组）")


class TestDatasetBase(BaseModel):
    """数据集基础 Schema"""
    name: str = Field(default="默认数据集", description="数据集名称")
    data_matrix: DataMatrix = Field(default_factory=DataMatrix, description="数据矩阵")
    description: Optional[str] = Field(None, description="数据集描述")


class TestDatasetCreate(TestDatasetBase):
    """创建数据集"""
    scenario_id: int = Field(..., description="所属场景ID")


class TestDatasetUpdate(BaseModel):
    """更新数据集"""
    name: Optional[str] = Field(None, description="数据集名称")
    data_matrix: Optional[DataMatrix] = Field(None, description="数据矩阵")
    description: Optional[str] = None


class TestDatasetResponse(TestDatasetBase):
    """数据集响应"""
    id: int
    scenario_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataDrivenExecutionResult(BaseModel):
    """数据驱动执行结果"""
    scenario_id: int
    scenario_name: str
    dataset_name: str
    total_iterations: int  # 总迭代次数
    success_iterations: int  # 成功次数
    failed_iterations: int  # 失败次数
    total_duration: int  # 总耗时 ms
    iterations: List[Dict[str, Any]] = []  # 每次迭代的结果
    # 每次迭代包含: iteration_index, data_row, step_results, success, duration, error


# 更新 forward reference
ApiGroupTree.model_rebuild()
