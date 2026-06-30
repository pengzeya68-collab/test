"""
AutoTest Pydantic Schema 模型
用于请求校验和响应序列化
"""

from pydantic import BaseModel, Field, BeforeValidator, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime


# 可空整数类型：自动将空字符串转换为 None
def empty_str_to_none(v):
    if v == "":
        return None
    return v


OptionalInt = Annotated[Optional[int], BeforeValidator(empty_str_to_none)]


# ========== 断言 target / operator 枚举 ==========

# 断言目标类型：标识从响应的哪个部分取值或做何种校验
ASSERTION_TARGET_TYPES = frozenset(
    {
        "status_code",  # HTTP 状态码
        "response_time",  # 响应时间（毫秒）
        "headers",  # 响应头整体
        "headers.<name>",  # 指定响应头字段
        "body",  # 响应体整体
        "response_body",
        "json_body",
        "json_body.<jsonpath>",  # 响应体 JSONPath 字段
        "response.<jsonpath>",
        "body.<jsonpath>",
        "json_schema",  # JSON Schema 断言：对整个响应体做 Schema 校验
    }
)

# JSON Schema 断言（target=json_schema）支持的操作符
JSON_SCHEMA_OPERATORS = frozenset({"matches", "not_matches"})


# ========== AutoTestGroup Schema ==========


class AutoTestGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="分组名称")
    parent_id: OptionalInt = Field(None, description="父级分组ID(null=根分组)")
    description: Optional[str] = Field(None, max_length=1000, description="分组描述")
    sort_order: int = Field(0, ge=0, description="同级排序(越小越靠前)")


class AutoTestGroupCreate(AutoTestGroupBase):
    pass


class AutoTestGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: OptionalInt = None
    description: Optional[str] = Field(None, max_length=1000)
    sort_order: Optional[int] = Field(None, ge=0)


class AutoTestGroupMove(BaseModel):
    """移动分组请求：改变 parent_id 和/或 sort_order"""

    parent_id: OptionalInt = Field(None, description="目标父分组ID(null=移到根)")
    sort_order: Optional[int] = Field(None, ge=0, description="新排序值")


class AutoTestGroupResponse(AutoTestGroupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

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
    payload: Optional[Any] = Field(None, description="请求体（JSON 类型为 dict，XML/Text 类型为 str）")
    assert_rules: Optional[List[Dict[str, Any]]] = Field(
        None,
        alias="assertions",
        description=(
            "断言规则列表，每条规则形如 {target, operator, expected}。"
            "target 取值见 ASSERTION_TARGET_TYPES，含 json_schema（JSON Schema 断言）。"
            "当 target=json_schema 时，使用 expected_schema 字段存储 JSON Schema，"
            "operator 取 matches/not_matches，见 JSON_SCHEMA_OPERATORS。"
        ),
    )
    extractors: Optional[List[Dict[str, Any]]] = Field(None, description="变量提取规则")
    description: Optional[str] = Field(None, description="用例描述")
    pre_script: Optional[str] = Field(None, description="前置脚本（JS/Python）")
    post_script: Optional[str] = Field(None, description="后置脚本（JS/Python）")
    pre_script_language: str = Field("javascript", description="前置脚本语言: javascript/python")
    post_script_language: str = Field("javascript", description="后置脚本语言: javascript/python")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="响应JSON Schema")

    model_config = ConfigDict(populate_by_name=True)


class AutoTestCaseCreate(AutoTestCaseBase):
    folder_id: OptionalInt = Field(None, description="所属文件夹ID")
    group_id: OptionalInt = Field(None, description="所属分组ID，兼容旧前端字段")

    @model_validator(mode="after")
    def validate_group_or_folder(self):
        if self.folder_id in (None, "") and self.group_id in (None, ""):
            raise ValueError("folder_id 或 group_id 必须提供一个")
        return self


class AutoTestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    body_type: Optional[str] = None
    content_type: Optional[str] = None
    payload: Optional[Any] = None
    assert_rules: Optional[List[Dict[str, Any]]] = Field(
        None,
        alias="assertions",
        description=(
            "断言规则列表，每条规则形如 {target, operator, expected}。"
            "target 取值见 ASSERTION_TARGET_TYPES，含 json_schema（JSON Schema 断言）。"
            "当 target=json_schema 时，使用 expected_schema 字段存储 JSON Schema，"
            "operator 取 matches/not_matches，见 JSON_SCHEMA_OPERATORS。"
        ),
    )
    extractors: Optional[List[Dict[str, Any]]] = Field(None, description="变量提取规则")
    description: Optional[str] = None
    folder_id: Optional[Any] = None
    group_id: Optional[Any] = None
    pre_script: Optional[str] = None
    post_script: Optional[str] = None
    pre_script_language: Optional[str] = "javascript"
    post_script_language: Optional[str] = "javascript"
    response_schema: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)


class AutoTestCaseResponse(AutoTestCaseBase):
    id: int
    folder_id: OptionalInt = None
    group_id: OptionalInt = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== AutoTestEnvironment Schema ==========


class AutoTestEnvironmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="环境名称")
    base_url: Optional[str] = Field(None, description="基础路径")
    variables: Dict[str, Any] = Field(default_factory=dict, description="全局变量")
    is_default: bool = Field(False, description="是否为默认环境")
    services: Optional[List[Dict[str, Any]]] = Field(None, description="多服务URL配置")
    # 父环境ID，用于变量继承（子环境覆盖父环境同名变量），最大继承深度 5 层
    parent_id: OptionalInt = Field(None, description="父环境ID(用于变量继承)")

    @model_validator(mode="before")
    @classmethod
    def normalize_env_name(cls, data):
        if isinstance(data, dict) and "name" not in data and data.get("env_name"):
            data = {**data, "name": data["env_name"]}
        return data


class AutoTestEnvironmentCreate(AutoTestEnvironmentBase):
    pass


class AutoTestEnvironmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    services: Optional[List[Dict[str, Any]]] = None
    parent_id: OptionalInt = Field(None, description="父环境ID(用于变量继承)")

    @model_validator(mode="before")
    @classmethod
    def normalize_env_name(cls, data):
        if isinstance(data, dict) and "name" not in data and data.get("env_name"):
            data = {**data, "name": data["env_name"]}
        return data


class AutoTestEnvironmentResponse(BaseModel):
    id: int
    name: Optional[str] = None  # 对应模型的 env_name，通过 model_validator 映射
    env_name: Optional[str] = None
    base_url: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False
    services: Optional[List[Dict[str, Any]]] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def map_env_name(cls, data):
        if isinstance(data, dict):
            if "name" not in data and data.get("env_name"):
                data = {**data, "name": data["env_name"]}
            if "env_name" not in data and data.get("name"):
                data = {**data, "env_name": data["name"]}
        else:
            # ORM 对象
            env_name = getattr(data, "env_name", None)
            if env_name:
                data_dict = {}
                for field in [
                    "id",
                    "base_url",
                    "variables",
                    "is_default",
                    "services",
                    "parent_id",
                    "created_at",
                ]:
                    data_dict[field] = getattr(data, field, None)
                data_dict["name"] = env_name
                data_dict["env_name"] = env_name
                # 父环境名称（若已加载关系则取，否则为 None）
                parent = getattr(data, "parent", None)
                data_dict["parent_name"] = getattr(parent, "env_name", None) if parent else None
                return data_dict
        return data


# ========== 环境变量继承 Schema ==========


class EffectiveVariableResponse(BaseModel):
    """合并后的有效变量（标注来源环境）"""

    name: str = Field(..., description="变量名")
    value: Any = Field(..., description="变量值（合并后）")
    source_environment_id: int = Field(..., description="变量来源环境ID")
    source_environment_name: str = Field(..., description="变量来源环境名称")
    is_overridden: bool = Field(
        False, description="是否被子环境覆盖（仅当此变量在更上层环境中也存在时为 True）"
    )

    model_config = ConfigDict(from_attributes=True)


class InheritanceChainItemResponse(BaseModel):
    """继承链中的单个环境条目"""

    id: int
    env_name: str
    name: Optional[str] = None
    parent_id: Optional[int] = None
    depth: int = Field(..., description="继承深度：0=根环境，逐层递增")

    model_config = ConfigDict(from_attributes=True)


# ========== AutoTestHistory Schema ==========


class AutoTestHistoryResponse(BaseModel):
    id: int
    case_id: int
    status: str
    execution_time: Optional[int] = None
    report_url: Optional[str] = None
    response_data: Optional[Any] = Field(None, description="接口实际响应内容，可能为dict, list或str")
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 执行结果 Schema ==========


class CaseRunRequest(BaseModel):
    env_id: OptionalInt = Field(None, description="环境ID")


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
    api_case_id: Optional[int] = Field(None, description="引用的接口ID")
    step_order: int = Field(default=0, description="执行顺序")
    is_active: bool = Field(True, description="是否启用")
    variable_overrides: Optional[Dict[str, Any]] = Field(None, description="局部变量覆盖")
    step_type: str = Field(
        default="api_request",
        description="步骤类型: api_request/if_condition/for_loop/for_each/wait/group/scenario_ref/db_query",
    )
    step_config: Optional[Dict[str, Any]] = Field(None, description="类型专属配置")
    parent_step_id: Optional[int] = Field(None, description="父步骤ID")
    pre_script: Optional[str] = Field(None, description="前置脚本（JS/Python）")
    post_script: Optional[str] = Field(None, description="后置脚本（JS/Python）")
    pre_script_language: str = Field("javascript", description="前置脚本语言: javascript/python")
    post_script_language: str = Field("javascript", description="后置脚本语言: javascript/python")


class ScenarioStepCreate(ScenarioStepBase):
    scenario_id: OptionalInt = Field(None, description="所属场景ID")


class ScenarioStepUpdate(BaseModel):
    api_case_id: OptionalInt = None
    step_order: Optional[int] = None
    is_active: Optional[bool] = None
    variable_overrides: Optional[Dict[str, Any]] = None
    step_type: Optional[str] = None
    step_config: Optional[Dict[str, Any]] = None
    parent_step_id: Optional[int] = None
    pre_script: Optional[str] = None
    post_script: Optional[str] = None
    pre_script_language: Optional[str] = "javascript"
    post_script_language: Optional[str] = "javascript"


class ScenarioStepResponse(ScenarioStepBase):
    id: int
    scenario_id: int
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
    webhook_token: Optional[str] = None
    user_id: Optional[int] = None
    schedule_cron_expression: Optional[str] = None
    schedule_env_id: Optional[int] = None
    schedule_webhook_url: Optional[str] = None
    schedule_task_name: Optional[str] = None
    schedule_is_active: Optional[bool] = None
    project_id: Optional[int] = None
    fail_fast: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


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
    scenario_id: OptionalInt = Field(None, description="所属场景ID；通常由路径参数提供")


class AutoTestDatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="数据集名称")
    data_matrix: Optional[DataMatrix] = Field(None, description="数据矩阵")
    description: Optional[str] = None
    scenario_id: OptionalInt = Field(None, description="所属场景ID")


class AutoTestDatasetResponse(AutoTestDatasetBase):
    id: int
    scenario_id: int
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
    scenario_id: int
    cron_expression: str
    env_id: OptionalInt = None
    webhook_url: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = True


class ScheduleTaskResponse(BaseModel):
    task_id: str
    job_id: str
    scenario_id: int
    env_id: OptionalInt = None
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


# ========== 测试数据工厂 Schema ==========

VALID_RULE_TYPES = {
    "fixed",
    "enum",
    "increment",
    "uuid",
    "timestamp",
    "date_offset",
    "phone",
    "email",
    "username",
    "env_ref",
}


class TemplateFieldRuleCreate(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=100, description="字段名")
    field_label: Optional[str] = Field(None, max_length=200, description="字段标签")
    rule_type: str = Field(
        ...,
        description="规则类型: fixed/enum/increment/uuid/timestamp/date_offset/phone/email/username/env_ref",
    )
    rule_config: Optional[Dict[str, Any]] = Field(None, description="规则配置")
    sort_order: int = Field(default=0, ge=0, description="排序")

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v):
        if v not in VALID_RULE_TYPES:
            raise ValueError(f"不支持的规则类型: {v}")
        return v


class TemplateFieldRuleResponse(TemplateFieldRuleCreate):
    id: int
    template_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestDataTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    scenario_id: Optional[int] = Field(None, gt=0, description="关联场景ID")
    row_count: int = Field(default=10, ge=1, le=100, description="生成行数(1-100)")
    fields: List[TemplateFieldRuleCreate] = Field(
        default_factory=list, min_length=1, max_length=20, description="字段规则列表(1-20个)"
    )

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v):
        for f in v:
            if f.rule_type not in VALID_RULE_TYPES:
                raise ValueError(f"不支持的规则类型: {f.rule_type}，支持的类型: {', '.join(sorted(VALID_RULE_TYPES))}")
        return v


class TestDataTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = None
    scenario_id: Optional[int] = Field(None, gt=0, description="关联场景ID")
    row_count: Optional[int] = Field(None, ge=1, le=100, description="生成行数(1-100)")
    fields: Optional[List[TemplateFieldRuleCreate]] = Field(
        None, min_length=1, max_length=20, description="字段规则列表(1-20个)"
    )

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v):
        if v is None:
            return v
        for f in v:
            if f.rule_type not in VALID_RULE_TYPES:
                raise ValueError(f"不支持的规则类型: {f.rule_type}，支持的类型: {', '.join(sorted(VALID_RULE_TYPES))}")
        return v


class TestDataTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_id: Optional[int] = None
    scenario_id: Optional[int] = None
    row_count: int = 10
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    fields: List[TemplateFieldRuleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class GeneratedDatasetResponse(BaseModel):
    dataset_id: int
    name: str
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0


# 重建前向引用
AutoTestGroupTree.model_rebuild()


# ========== 数据库连接 Schema ==========


class DBConnectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="连接名称")
    db_type: str = Field(..., description="数据库类型: mysql/postgresql/mongodb/redis")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., ge=1, le=65535, description="端口")
    database_name: Optional[str] = Field(None, description="数据库名")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码（创建/更新时传入明文，响应时不返回）")
    is_active: bool = Field(True, description="是否启用")


class DBConnectionCreate(DBConnectionBase):
    pass


class DBConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class DBConnectionResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool = True
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== 用例版本管理 Schema ==========


class CaseVersionCreate(BaseModel):
    """创建版本请求：version_number 留空时自动递增生成 v1/v2/v3..."""

    version_number: Optional[str] = Field(
        None, max_length=50, description="版本号(留空自动递增 v1/v2/v3...)"
    )
    version_label: Optional[str] = Field(None, max_length=200, description="版本标签")


class CaseVersionResponse(BaseModel):
    """版本响应（列表与详情共用，详情额外携带 snapshot 字段）"""

    id: int
    case_id: int
    version_number: str
    version_label: Optional[str] = None
    snapshot: Optional[Dict[str, Any]] = Field(
        None, description="完整用例快照(列表接口不返回,详情接口返回)"
    )
    created_by: Optional[int] = None
    created_at: datetime
    is_current: bool = False

    model_config = ConfigDict(from_attributes=True)


class CaseVersionDiffItem(BaseModel):
    """单个字段差异"""

    field: str = Field(..., description="字段路径,如 headers.Authorization / payload.username")
    old_value: Any = Field(None, description="旧版本值(被删除时为 None)")
    new_value: Any = Field(None, description="新版本值(被删除时为 None)")
    change_type: str = Field(
        ..., description="变更类型: added(新增) / removed(删除) / modified(修改)"
    )


class CaseVersionDiffResponse(BaseModel):
    """两个版本对比结果"""

    v1: Dict[str, Any] = Field(..., description="旧版本摘要 {id, version_number, version_label}")
    v2: Dict[str, Any] = Field(..., description="新版本摘要 {id, version_number, version_label}")
    diffs: List[CaseVersionDiffItem] = Field(..., description="差异列表")
    total_changes: int = Field(..., description="差异总数")
    is_identical: bool = Field(..., description="两版本是否完全一致")
