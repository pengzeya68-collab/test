"""
测试环境 Schema
"""

from pydantic import BaseModel, ConfigDict, BeforeValidator
from datetime import datetime
from typing import Optional, Annotated


def _empty_str_to_none(v):
    if v == "":
        return None
    return v


OptionalInt = Annotated[Optional[int], BeforeValidator(_empty_str_to_none)]


class EnvironmentBase(BaseModel):
    name: str
    base_url: Optional[str] = None
    variables: Optional[str] = None
    is_default: Optional[bool] = False
    # 父环境ID，用于变量继承；为空表示无父环境
    parent_id: OptionalInt = None


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(EnvironmentBase):
    name: Optional[str] = None


class EnvironmentResponse(EnvironmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
