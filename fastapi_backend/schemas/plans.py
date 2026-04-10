"""
测试计划 Schema
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class TestPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    environment_id: Optional[int] = None
    case_ids: List[int]


class TestPlanCreate(TestPlanBase):
    pass


class TestPlanUpdate(TestPlanBase):
    name: Optional[str] = None
    description: Optional[str] = None


class TestPlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    environment_id: Optional[int]
    environment_name: Optional[str]
    case_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
