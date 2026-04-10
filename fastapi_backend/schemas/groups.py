"""
接口分组 Schema
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class ApiGroupBase(BaseModel):
    """分组基础信息"""
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class ApiGroupCreate(ApiGroupBase):
    """创建分组"""
    pass


class ApiGroupUpdate(ApiGroupBase):
    """更新分组"""
    name: Optional[str] = None


class ApiGroupResponse(ApiGroupBase):
    """分组响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiGroupTreeNode(ApiGroupResponse):
    """分组树形节点"""
    children: List[ApiGroupTreeNode] = []

    model_config = ConfigDict(from_attributes=True)
