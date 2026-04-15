from pydantic import BaseModel, Field, model_validator

from fastapi_backend.core.config import settings


class SandboxRequest(BaseModel):
    code: str = Field(..., min_length=1, description="需要执行的代码")
    language: str = Field(default="python", description="编程语言：python, sql, shell")
    input_data: str | None = Field(None, description="输入数据，将传递给程序的标准输入")
    timeout: int = Field(
        default=settings.SANDBOX_DEFAULT_TIMEOUT_SECONDS,
        ge=1,
        le=settings.SANDBOX_MAX_TIMEOUT_SECONDS,
        description=f"执行超时时间（秒），最大 {settings.SANDBOX_MAX_TIMEOUT_SECONDS} 秒"
    )


class SandboxResult(BaseModel):
    exit_code: int = Field(..., description="进程退出码，超时或内部错误时为 -1")
    stdout: str = Field(default="", description="标准输出内容")
    stderr: str = Field(default="", description="标准错误内容")
    execution_time_ms: int = Field(..., ge=0, description="执行耗时（毫秒）")
    success: bool = Field(default=False, description="执行是否成功（exit_code == 0）")
    returncode: int = Field(default=0, description="兼容字段，同 exit_code")

    @model_validator(mode='after')
    def compute_computed_fields(self):
        self.success = self.exit_code == 0
        self.returncode = self.exit_code
        return self
