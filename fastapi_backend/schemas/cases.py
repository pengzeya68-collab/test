"""
接口用例 Schema
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ApiCaseBase(BaseModel):
    """用例基础信息"""
    group_id: Optional[int] = None
    name: str
    method: str
    url: str
    description: Optional[str] = None
    headers: Optional[str] = None
    body: Optional[str] = None
    body_type: Optional[str] = "json"
    assert_rules: Optional[str] = None


class ApiCaseCreate(ApiCaseBase):
    """创建用例"""
    pass


class ApiCaseUpdate(ApiCaseBase):
    """更新用例"""
    group_id: Optional[int] = None
    name: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None


class ApiCaseResponse(ApiCaseBase):
    """用例响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    group_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApiCaseListResponse(BaseModel):
    """用例列表分页响应"""
    total: int
    items: list[ApiCaseResponse]
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
