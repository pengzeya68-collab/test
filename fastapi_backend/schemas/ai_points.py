"""AI 积分相关 Schema"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


# ──────────── 积分配置 ────────────


class AIPointsConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature: str
    display_name: str
    points_cost: int
    description: Optional[str] = None


class AIPointsConfigUpdate(BaseModel):
    points_cost: Optional[int] = Field(None, ge=0, description="积分消耗")
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)


# ──────────── 使用日志 ────────────


class AIUsageLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: Optional[str] = None
    feature: str
    feature_name: Optional[str] = None
    points_cost: int
    created_at: Optional[datetime] = None


class AIUsageStatsResponse(BaseModel):
    feature: str
    display_name: str
    total_calls: int
    total_points: int


# ──────────── 积分流水 ────────────


class PointsTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: Optional[str] = None
    amount: int
    balance_after: int
    tx_type: str
    tx_type_name: Optional[str] = None
    source: Optional[str] = None
    related_feature: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None


class PointsBalanceResponse(BaseModel):
    points: int
    level: int


class PointsPurchaseRequest(BaseModel):
    """管理员手动充值"""

    user_id: int = Field(..., description="用户ID")
    amount: int = Field(..., gt=0, description="充值积分数量")
    note: Optional[str] = Field(None, max_length=255, description="备注")


class PointsPageResponse(BaseModel):
    """积分流水列表响应"""

    items: list[PointsTransactionResponse]
    total: int
    page: int
    page_size: int


class UserUsageStatsResponse(BaseModel):
    """用户 AI 使用统计"""

    items: list[AIUsageStatsResponse]
    total_points_used: int
