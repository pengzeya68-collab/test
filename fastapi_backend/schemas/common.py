from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")
ItemT = TypeVar("ItemT")


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    """统一错误响应格式"""
    detail: str
    code: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: datetime = datetime.now()


class SuccessResponse(BaseModel, Generic[T]):
    """通用成功响应"""
    success: bool = True
    data: T
    message: Optional[str] = None


class PaginationResponse(BaseModel, Generic[ItemT]):
    """分页响应"""
    items: list[ItemT]
    total: int
    page: int
    size: int
    pages: int
