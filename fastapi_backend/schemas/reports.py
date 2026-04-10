"""
测试报告 Schema
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class TestReportResultResponse(BaseModel):
    """单个测试结果响应"""
    id: int
    case_id: Optional[int]
    case_name: Optional[str]
    method: Optional[str]
    url: Optional[str]
    status_code: Optional[int]
    success: bool
    time_ms: Optional[int]
    error: Optional[str]
    request_headers: Optional[str]
    request_body: Optional[str]
    response_body: Optional[str]
    response_headers: Optional[str]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestReportResponse(BaseModel):
    """测试报告响应"""
    id: int
    plan_id: Optional[int]
    plan_name: Optional[str]
    total_count: int
    success_count: int
    failed_count: int
    total_time: int
    status: str
    executed_at: datetime
    results: Optional[List[TestReportResultResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class TestReportListResponse(BaseModel):
    """测试报告列表响应"""
    total: int
    items: list[TestReportResponse]
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
