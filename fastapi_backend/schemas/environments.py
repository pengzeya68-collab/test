"""
测试环境 Schema
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class EnvironmentBase(BaseModel):
    name: str
    base_url: Optional[str] = None
    variables: Optional[str] = None
    is_default: Optional[bool] = False


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(EnvironmentBase):
    name: Optional[str] = None


class EnvironmentResponse(EnvironmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
