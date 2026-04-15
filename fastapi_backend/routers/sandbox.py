"""
代码沙箱路由 - 安全执行用户代码
"""
from fastapi import APIRouter, Depends

from fastapi_backend.schemas.common import SuccessResponse
from fastapi_backend.schemas.sandbox import SandboxRequest, SandboxResult
from fastapi_backend.services.sandbox_service import CodeSandbox
from fastapi_backend.deps.auth import get_current_user

router = APIRouter(prefix="/api/v1/sandbox", tags=["代码沙箱"], dependencies=[Depends(get_current_user)])


def get_sandbox() -> CodeSandbox:
    return CodeSandbox()


@router.post("/execute", response_model=SuccessResponse[SandboxResult])
async def execute_code(
    request: SandboxRequest,
    sandbox: CodeSandbox = Depends(get_sandbox)
):
    """
    安全执行用户提交的代码，支持多种语言
    """
    result_dict = await sandbox.execute_code(
        code=request.code,
        language=request.language,
        input_data=request.input_data,
        timeout=request.timeout
    )

    # 将字典转换为SandboxResult模型
    result = SandboxResult(**result_dict)
    return SuccessResponse(
        data=result,
        message="代码执行完成"
    )