"""
统一异常处理模块 - 业务异常类定义
"""
from typing import Any, Optional


class BusinessException(Exception):
    """基础业务异常"""

    def __init__(
        self,
        detail: str,
        code: Optional[str] = None,
        status_code: int = 400,
        extra: Optional[dict[str, Any]] = None
    ):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(detail)


class AuthenticationException(BusinessException):
    """认证失败异常 (401)"""

    def __init__(self, detail: str = "认证失败", code: Optional[str] = None):
        super().__init__(detail, code or "AUTH_ERROR", status_code=401)


class AuthorizationException(BusinessException):
    """权限不足异常 (403)"""

    def __init__(self, detail: str = "权限不足", code: Optional[str] = None):
        super().__init__(detail, code or "FORBIDDEN", status_code=403)


class NotFoundException(BusinessException):
    """资源不存在异常 (404)"""

    def __init__(self, detail: str = "资源不存在", code: Optional[str] = None):
        super().__init__(detail, code or "NOT_FOUND", status_code=404)


class ValidationException(BusinessException):
    """参数校验异常 (422)"""

    def __init__(self, detail: str = "参数校验失败", code: Optional[str] = None):
        super().__init__(detail, code or "VALIDATION_ERROR", status_code=422)